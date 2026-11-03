from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class SlotResponse(BaseModel):
    start: datetime = Field(validation_alias=AliasChoices("start", "start_date"))
    end: datetime
    available: bool

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ")},
    )
