import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import TenantMixin, TimestampMixin, UUIDMixin
from core.database import Base


class NotificationLog(UUIDMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "notification_logs"

    channel: Mapped[str] = mapped_column(String(32))  # email | telegram | push | speaker
    level: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16))  # sent | failed
    error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    alert_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
