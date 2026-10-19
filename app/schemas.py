from datetime import time
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.models import Direction, Status


def _blank_note(value: str | None) -> str | None:
    if value is None:
        return None
    return value or None


class CrossingCreate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "departure": "21:40",
                    "berth": 2,
                    "direction": "island_to_city",
                    "note": "Ждёт опаздывающий автобус",
                    "capacity": 36,
                }
            ]
        },
    )

    departure: time
    berth: int = Field(ge=1, le=4)
    direction: Direction
    note: str | None = Field(default=None, max_length=280)
    capacity: int = Field(ge=1, le=80)

    @field_validator("note")
    @classmethod
    def note_or_none(cls, value: str | None) -> str | None:
        return _blank_note(value)


class CrossingUpdate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)

    departure: time | None = None
    berth: int | None = Field(default=None, ge=1, le=4)
    direction: Direction | None = None
    note: str | None = Field(default=None, max_length=280)
    capacity: int | None = Field(default=None, ge=1, le=80)

    @field_validator("note")
    @classmethod
    def note_or_none(cls, value: str | None) -> str | None:
        return _blank_note(value)


class StatusChange(BaseModel):
    status: Status


class CrossingOut(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str
    departure: time
    berth: int
    direction: Direction
    status: Status
    note: str | None
    capacity: int

    @field_serializer("departure")
    def departure_hhmm(self, value: time) -> str:
        return value.strftime("%H:%M")


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
