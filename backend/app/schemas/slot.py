from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class SlotResponse(BaseModel):
    start: datetime = Field(validation_alias=AliasChoices("start", "start_date"))
    end: datetime
    available: bool
    held: bool = False

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ")},
    )


class SlotHoldRequest(BaseModel):
    slot_start: datetime = Field(validation_alias=AliasChoices("slot_start", "slotStart"))

    model_config = ConfigDict(populate_by_name=True)


class SlotHoldResponse(BaseModel):
    success: bool = True
    slot_start: datetime = Field(
        validation_alias=AliasChoices("slot_start", "slotStart"),
        serialization_alias="slotStart",
    )
    remaining_seconds: int = Field(
        validation_alias=AliasChoices("remaining_seconds", "remainingSeconds"),
        serialization_alias="remainingSeconds",
    )
    message: str

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ")},
    )


class SlotReleaseHoldRequest(BaseModel):
    slot_start: datetime = Field(validation_alias=AliasChoices("slot_start", "slotStart"))

    model_config = ConfigDict(populate_by_name=True)
