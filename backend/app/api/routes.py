from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user_id
from app.schemas.slot import SlotResponse
from sqlalchemy.ext.asyncio import AsyncSession

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
