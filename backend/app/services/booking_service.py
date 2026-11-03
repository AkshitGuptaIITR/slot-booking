# backend/app/services/booking_service.py
from datetime import datetime, timezone, timedelta
from typing import Sequence
import uuid
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BookingLimitReachedException,
    IdempotencyKeyReusedException,
    SlotTakenException,
    SlotHeldException,
    BookingNotFoundException,
    CancellationWindowClosedException,
)
from app.core.security import compute_request_hash
from app.models.booking import Booking, BookingStatus
from app.models.idempotency import IdempotencyRecord
from app.schemas.booking import BookingCreateRequest
from app.services.slot_service import validate_booking_slot
from app.services.hold_service import hold_service
from app.services.lock_service import lock_service


async def get_user_bookings(
    user_id: str,
    db: AsyncSession,
) -> Sequence[Booking]:
    """Retrieves all bookings (active, past, and cancelled) for a user,

    ordered by slot start time ascending.
    """
    stmt = (
        select(Booking)
        .where(Booking.user_id == user_id)
        .order_by(Booking.slot_start.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_booking(
    payload: BookingCreateRequest,
    user_id: str,
    idempotency_key: str,
    db: AsyncSession,
) -> tuple[dict, int]:
    """Processes booking creation with idempotency and concurrency guards.

    Returns a tuple of (response_body_dict, status_code).
    """
    # 1. Compute request hash from payload
    request_data = payload.model_dump(mode="json", by_alias=True)
    request_hash = compute_request_hash(request_data)

    # 2. Check Idempotency Record
    idemp_stmt = select(IdempotencyRecord).where(
        IdempotencyRecord.user_id == user_id,
        IdempotencyRecord.key == idempotency_key,
    )
    idemp_result = await db.execute(idemp_stmt)
    existing_record = idemp_result.scalar_one_or_none()

    if existing_record:
        if existing_record.request_hash == request_hash:
            # Deterministic replay of original response
            return existing_record.response_body, existing_record.response_code
        else:
            raise IdempotencyKeyReusedException(
                "Idempotency key was previously used with a different request payload"
            )

    # 3. Validate Slot Rules (aligned to 30 mins, 09:00-17:00 IST, Monday-Friday, <= 14 days)
    validate_booking_slot(payload.slot_start)

    # 4. Concurrency Control: Lock on user_id serializes concurrent booking requests
    # by the SAME user, strictly preventing race conditions against the 2-booking limit.
    await lock_service.acquire_user_lock(db, user_id)

    # 5. Check Active Upcoming Booking Limit (Max 2 per user)
    now_utc = datetime.now(timezone.utc)
    count_stmt = select(func.count(Booking.id)).where(
        Booking.user_id == user_id,
        Booking.status == BookingStatus.ACTIVE,
        Booking.slot_start >= now_utc,
    )
    active_count = await db.scalar(count_stmt) or 0
    if active_count >= 2:
        raise BookingLimitReachedException(
            "User cannot have more than 2 active upcoming bookings at any time"
        )

    # 6. Check if slot is currently held by another user
    slot_start_iso = payload.slot_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    if hold_service.is_held_by_other(slot_start_iso, user_id):
        raise SlotHeldException("This slot is temporarily on hold by another user")

    # 7. Check if slot is already actively booked
    existing_slot_stmt = select(Booking.id).where(
        Booking.slot_start == payload.slot_start,
        Booking.status == BookingStatus.ACTIVE,
    )
    if await db.scalar(existing_slot_stmt):
        raise SlotTakenException("This slot is already booked")

    # 8. Insert Booking inside a savepoint to catch slot collision
    new_booking = Booking(
        user_id=user_id,
        name=payload.name,
        email=payload.email,
        slot_start=payload.slot_start,
        status=BookingStatus.ACTIVE,
    )

    try:
        async with db.begin_nested():
            db.add(new_booking)
            await db.flush()
    except IntegrityError:
        # Triggered if idx_unique_active_slot detects another ACTIVE booking on this slot
        raise SlotTakenException("This slot is already booked")

    # 9. Prepare response payload
    response_body = {
        "id": str(new_booking.id),
        "slotStart": new_booking.slot_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "name": new_booking.name,
        "email": new_booking.email,
        "status": new_booking.status.value,
    }
    status_code = 201

    # 10. Record Idempotency Result
    idempotency_entry = IdempotencyRecord(
        user_id=user_id,
        key=idempotency_key,
        request_hash=request_hash,
        response_code=status_code,
        response_body=response_body,
    )
    db.add(idempotency_entry)

    # Commit entire transaction
    await db.commit()

    # Release any active hold for this user now that booking is confirmed
    hold_service.release_hold(slot_start_iso, user_id)

    return response_body, status_code


async def cancel_booking(
    booking_id: uuid.UUID, user_id: str, db: AsyncSession
) -> None:
    """Cancels an upcoming active booking for the authenticated user.

    - Returns 404 NOT_FOUND for non-existent or other users' bookings.
    - Idempotent: returns without error (204) if the booking is already cancelled.
    - Returns 409 CANCELLATION_WINDOW_CLOSED if within 2 hours of slot start (or already past).
    """
    now_utc = datetime.now(timezone.utc)

    # 1. Fetch the booking scoped to user_id
    stmt = (
        select(Booking)
        .where(
            Booking.id == booking_id,
            Booking.user_id == user_id,
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()

    # 2. Return 404 for missing or unowned bookings
    if not booking:
        raise BookingNotFoundException("Booking not found")

    # 3. Cancelling an already-cancelled booking is idempotent (returns 204)
    if booking.status == BookingStatus.CANCELLED:
        return

    # 4. Check 2-hour minimum notice requirement
    slot_start = booking.slot_start
    if slot_start.tzinfo is None:
        slot_start = slot_start.replace(tzinfo=timezone.utc)

    if slot_start < now_utc + timedelta(hours=2):
        raise CancellationWindowClosedException(
            "Bookings cannot be cancelled within 2 hours of the slot start time"
        )

    # 5. Mutate status and update cancellation timestamp
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = now_utc

    await db.commit()
