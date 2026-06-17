import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_code: str
    name: str
    face_id: int | None
    camera_id: str | None
    type: str
    score: float
    image_url: str | None
    created_at: datetime


class ShiftCreate(BaseModel):
    name: str
    start_time: str
    end_time: str
    grace_minutes: int = 15
    applies_to: str = "Toàn công ty"
    color: str = "eco-green"


class ShiftUpdate(BaseModel):
    name: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    grace_minutes: int | None = None
    applies_to: str | None = None
    color: str | None = None
    active: bool | None = None


class ShiftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    start_time: str
    end_time: str
    grace_minutes: int
    applies_to: str
    color: str
    active: bool


class ReportRow(BaseModel):
    employee_code: str
    name: str
    work_days: int
    late: int
    early: int
    total_hours: float


class ReportResponse(BaseModel):
    metrics: dict
    rows: list[ReportRow]
