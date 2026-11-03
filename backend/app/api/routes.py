import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_current_user_id, get_idempotency_key
from app.schemas.booking import BookingCreateRequest, BookingResponse
from app.schemas.slot import SlotResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.booking_service import (
    create_booking,
    get_user_bookings,
    cancel_booking,
)
from app.services.slot_service import get_slots_for_date
from app.db.session import get_db

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
    return await get_slots_for_date(date_str=date, db=db)


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
