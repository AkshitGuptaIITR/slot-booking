from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidDateException, InvalidSlotException
from app.models.booking import Booking, BookingStatus
from app.schemas.slot import SlotResponse

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
SLOT_DURATION_MINUTES = 30
WORK_START_HOUR = 9
WORK_END_HOUR = 17


def validate_booking_slot(slot_start: datetime) -> None:
    if slot_start.tzinfo is None:
        slot_start = slot_start.replace(tzinfo=timezone.utc)
    else:
        slot_start = slot_start.astimezone(timezone.utc)

    if slot_start.second != 0 or slot_start.microsecond != 0:
        raise InvalidSlotException("Slot time must not contain seconds or microseconds")

    if slot_start.minute not in (0, 30):
        raise InvalidSlotException(
            "Slot time must start on the hour (:00) or half-hour (:30)"
        )

    now_utc = datetime.now(timezone.utc)
    max_advance_utc = now_utc + timedelta(days=14)

    if slot_start <= now_utc:
        raise InvalidSlotException("Cannot book a slot in the past")

    if slot_start > max_advance_utc:
        raise InvalidSlotException("Cannot book a slot more than 14 days ahead")

    slot_ist = slot_start.astimezone(KOLKATA_TZ)

    if slot_ist.weekday() >= 5:
        raise InvalidSlotException(
            "Slots cannot be booked on weekends. The consultant works Monday to Friday only."
        )

    earliest_slot_time = time(WORK_START_HOUR, 0)
    latest_slot_time = time(WORK_END_HOUR - 1, 30)

    if not (earliest_slot_time <= slot_ist.time() <= latest_slot_time):
        raise InvalidSlotException(
            f"Slot must fall within working hours (09:00-17:00 Asia/Kolkata). "
            f"Requested slot time in IST: {slot_ist.strftime('%H:%M')}"
        )


def parse_calendar_date(date_str: str) -> date:
    try:
        parsed_date = date.fromisoformat(date_str)
        # Prevent partial year formats or unusual representations
        if len(date_str) != 10 or date_str.count("-") != 2:
            raise ValueError
        return parsed_date
    except (ValueError, TypeError):
        raise InvalidDateException(
            "Query parameter 'date' must be in YYYY-MM-DD format"
        )


async def get_slots_for_date(
    date_str: str,
    db: AsyncSession,
) -> list[SlotResponse]:
    target_date = parse_calendar_date(date_str)

    # Consultant works Monday to Friday only (weekday 5 is Saturday, 6 is Sunday)
    if target_date.weekday() >= 5:
        return []

    # 1. Define working hours in Asia/Kolkata
    day_start_ist = datetime.combine(
        target_date, time(WORK_START_HOUR, 0), tzinfo=KOLKATA_TZ
    )
    day_end_ist = datetime.combine(
        target_date, time(WORK_END_HOUR, 0), tzinfo=KOLKATA_TZ
    )

    # 2. Convert boundary window to UTC for DB querying
    day_start_utc = day_start_ist.astimezone(timezone.utc)
    day_end_utc = day_end_ist.astimezone(timezone.utc)

    # 3. Fetch all active bookings in this window
    stmt = select(Booking.slot_start).where(
        Booking.slot_start >= day_start_utc,
        Booking.slot_start < day_end_utc,
        Booking.status == BookingStatus.ACTIVE,
    )
    result = await db.execute(stmt)
    booked_starts = {row[0] for row in result.all()}

    # 4. Generate all 16 slots and determine availability
    now_utc = datetime.now(timezone.utc)
    max_advance_utc = now_utc + timedelta(days=14)

    slots: list[SlotResponse] = []
    current_ist = day_start_ist

    while current_ist < day_end_ist:
        slot_end_ist = current_ist + timedelta(minutes=SLOT_DURATION_MINUTES)

        slot_start_utc = current_ist.astimezone(timezone.utc)
        slot_end_utc = slot_end_ist.astimezone(timezone.utc)

        # A slot is available ONLY if:
        # - It is not already booked
        # - It is not in the past
        # - It is not more than 14 days in the future
        is_booked = slot_start_utc in booked_starts
        is_past = slot_start_utc <= now_utc
        is_too_far = slot_start_utc > max_advance_utc

        is_available = not (is_booked or is_past or is_too_far)

        slots.append(
            SlotResponse(
                start=slot_start_utc,
                end=slot_end_utc,
                available=is_available,
            )
        )
        current_ist = slot_end_ist

    return slots
