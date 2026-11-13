from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6, max_length=72)


class ClubIn(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = ""


class ClubOut(ClubIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    manager_id: int


class EventIn(BaseModel):
    club_id: int
    title: str = Field(min_length=3, max_length=150)
    description: str = ""
    location: str = Field(min_length=1, max_length=150)
    start_time: datetime
    end_time: datetime
    capacity: int = Field(gt=0, le=5000)
    points: int = Field(default=5, ge=0, le=20)
    poster_url: str | None = None

    @model_validator(mode="after")
    def check_time(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time phải sau start_time")
        return self


class EventOut(EventIn):
    id: int
    registered_count: int = 0


class MembershipPatch(BaseModel):
    status: Literal["approved", "rejected"]


class CheckinIn(BaseModel):
    code: str = Field(min_length=1, max_length=20)