import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from apps.alerts.models import AlertLevel, AlertStatus


class AlertCreate(BaseModel):
    source_type: str
    source_id: str | None = None
    kind: str
    level: AlertLevel
    image_url: str | None = None
    clip_url: str | None = None
    payload: dict = {}


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: str
    source_id: str | None
    kind: str
    level: AlertLevel
    status: AlertStatus
    image_url: str | None
    clip_url: str | None
    payload: dict
    acked_by: uuid.UUID | None
    acked_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
