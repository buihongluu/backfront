import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import TenantMixin, TimestampMixin, UUIDMixin
from core.database import Base


class AlertLevel(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AlertStatus(str, enum.Enum):
    new = "new"
    ack = "ack"
    resolved = "resolved"


class Alert(UUIDMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "alerts"

    source_type: Mapped[str] = mapped_column(String(32))  # camera | radar | sensor | ai
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(64))  # fire | ppe | person | stroke | fall ...
    level: Mapped[AlertLevel] = mapped_column(Enum(AlertLevel, name="alert_level"))
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, name="alert_status"), default=AlertStatus.new, index=True
    )
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    clip_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)

    acked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    acked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
