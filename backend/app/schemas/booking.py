from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer

from app.models.booking import BookingStatus


class BookingCreateRequest(BaseModel):
    slot_start: datetime
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class BookingResponse(BaseModel):
    id: uuid.UUID
    slot_start: datetime
    name: str
    email: str
    status: BookingStatus

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={datetime: lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ")},
    )

    @field_serializer("slot_start")
    def serialize_slot_start(self, dt: datetime, _info) -> str:
        # Ensures UTC timestamp formatting with 'Z' suffix
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
