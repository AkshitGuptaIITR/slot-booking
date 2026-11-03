# backend/app/services/booking_service.py
from datetime import datetime, timezone
from typing import Sequence
import uuid
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BookingLimitReachedException,
    IdempotencyKeyReusedException,
    SlotTakenException,
    BookingAlreadyCancelledException,
    BookingNotFoundException,
)
from app.core.security import compute_request_hash
from app.models.booking import Booking, BookingStatus
from app.models.idempotency import IdempotencyRecord
from app.schemas.booking import BookingCreateRequest
from app.services.slot_service import validate_booking_slot


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
    request_data = payload.model_dump(mode="json")
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

    # 3. Validate Slot Rules (aligned to 30 mins, 09:00-17:00 IST, Mon-Fri, <= 14 days)
    validate_booking_slot(payload.slotStart)

    # 4. Transaction & Concurrency Control
    # Lock on user_id prevents concurrent requests from exceeding the 2-booking limit
    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:user_id))"),
        {"user_id": user_id},
    )

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

    # 6. Insert Booking inside a savepoint to catch slot collision
    new_booking = Booking(
        user_id=user_id,
        name=payload.name,
        email=payload.email,
        slot_start=payload.slotStart,
        status=BookingStatus.ACTIVE,
    )

    try:
        async with db.begin_nested():
            db.add(new_booking)
            await db.flush()
    except IntegrityError:
        # Triggered if idx_unique_active_slot detects another ACTIVE booking on this slot
        raise SlotTakenException("This slot is already booked")

    # 7. Prepare response payload
    response_body = {
        "id": str(new_booking.id),
        "slotStart": new_booking.slot_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "name": new_booking.name,
        "email": new_booking.email,
        "status": new_booking.status.value,
    }
    status_code = 201

    # 8. Record Idempotency Result
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

    return response_body, status_code


async def cancel_booking(
    booking_id: uuid.UUID, user_id: str, db: AsyncSession
) -> Booking:
    """Cancels an upcoming active booking for the authenticated user.

    Treats non-existent, unowned, or past bookings uniformly as 404 NOT_FOUND.
    """
    now_utc = datetime.now(timezone.utc)

    # 1. Fetch only if the booking belongs to user AND is scheduled in the future
    stmt = (
        select(Booking)
        .where(
            Booking.id == booking_id,
            Booking.user_id == user_id,
            Booking.slot_start > now_utc,
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()

    # 2. Return 404 for missing, unowned, or expired bookings
    if not booking:
        raise BookingNotFoundException("Booking not found")

    # 3. Check if an upcoming booking is already cancelled
    if booking.status == BookingStatus.CANCELLED:
        raise BookingAlreadyCancelledException("Booking is already cancelled")

    # 4. Mutate status and update cancellation timestamp
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = now_utc

    await db.commit()
    await db.refresh(booking)

    return booking
