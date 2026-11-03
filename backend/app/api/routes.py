import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_idempotency_key
from app.core.exceptions import SlotHeldException, SlotTakenException
from app.db.session import get_db
from app.models.booking import Booking, BookingStatus
from app.schemas.booking import BookingCreateRequest, BookingResponse
from app.schemas.slot import (
    SlotHoldRequest,
    SlotHoldResponse,
    SlotReleaseHoldRequest,
    SlotResponse,
)
from app.services.booking_service import (
    cancel_booking,
    create_booking,
    get_user_bookings,
)
from app.services.hold_service import hold_service
from app.services.slot_service import get_slots_for_date, validate_booking_slot

router = APIRouter()


@router.get(
    "/slots",
    response_model=list[SlotResponse],
    summary="Get slots for a specific date in Asia/Kolkata",
)
async def get_slots(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_slots_for_date(date_str=date, db=db, user_id=user_id)


@router.post(
    "/slots/hold",
    response_model=SlotHoldResponse,
    summary="Temporarily hold an available slot before opening booking form",
)
async def hold_slot(
    payload: SlotHoldRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Attempts to acquire a temporary in-memory hold on a slot for 2 minutes.

    Prevents multiple users from opening the booking form on the same slot simultaneously.
    """
    # 1. Validate slot bounds and working hours
    validate_booking_slot(payload.slot_start)

    # 2. Verify the slot isn't already actively booked in PostgreSQL
    stmt = select(Booking.id).where(
        Booking.slot_start == payload.slot_start,
        Booking.status == BookingStatus.ACTIVE,
    )
    if await db.scalar(stmt):
        raise SlotTakenException("This slot is already booked")

    # 3. Attempt to acquire in-memory hold
    slot_start_iso = payload.slot_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    acquired = hold_service.acquire_hold(slot_start=slot_start_iso, user_id=user_id)
    if not acquired:
        raise SlotHeldException("This slot is temporarily on hold by another user")

    hold_info = hold_service.get_hold_info(slot_start_iso)
    remaining_seconds = hold_info["remaining_seconds"] if hold_info else 120

    return SlotHoldResponse(
        success=True,
        slot_start=payload.slot_start,
        remaining_seconds=remaining_seconds,
        message="Slot held successfully for 2 minutes",
    )


@router.post(
    "/slots/release-hold",
    summary="Release a temporary hold if the user cancels or closes modal",
)
async def release_slot_hold(
    payload: SlotReleaseHoldRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Releases the in-memory hold if owned by this user."""
    slot_start_iso = payload.slot_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    released = hold_service.release_hold(slot_start=slot_start_iso, user_id=user_id)
    return {"success": released, "message": "Hold released" if released else "No active hold found"}


@router.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
)
async def post_booking(
    payload: BookingCreateRequest,
    user_id: str = Depends(get_current_user_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db),
):
    response_body, status_code = await create_booking(
        payload=payload,
        user_id=user_id,
        idempotency_key=idempotency_key,
        db=db,
    )
    return JSONResponse(status_code=status_code, content=response_body)


@router.get(
    "/bookings",
    response_model=list[BookingResponse],
    summary="List all bookings for the authenticated user",
)
async def list_bookings(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_user_bookings(user_id=user_id, db=db)


@router.delete(
    "/bookings/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel an active booking",
)
async def delete_booking(
    booking_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await cancel_booking(
        booking_id=booking_id,
        user_id=user_id,
        db=db,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
