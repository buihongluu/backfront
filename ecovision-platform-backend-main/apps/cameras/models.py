from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.devices.models import DeviceStatus
from core.base_model import TenantMixin, TimestampMixin, UUIDMixin
from core.database import Base


class Camera(UUIDMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "cameras"

    name: Mapped[str] = mapped_column(String(255))
    rtsp_url: Mapped[str] = mapped_column(String(512))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cluster: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # AI (FEAT-VMS-07)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    analyze_fps: Mapped[int] = mapped_column(Integer, default=3)

    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus, name="device_status"), default=DeviceStatus.offline
    )
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
