import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel: str
    level: str
    title: str
    status: str
    error: str | None
    alert_id: uuid.UUID | None
    created_at: datetime


class TestRequest(BaseModel):
    channel: str  # email | telegram | push | speaker
