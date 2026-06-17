import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import TenantMixin, TimestampMixin, UUIDMixin
from core.database import Base


class DeviceType(str, enum.Enum):
    camera = "camera"
    radar = "radar"
    speaker = "speaker"  # loa cảnh báo kết nối mạng riêng
    gateway = "gateway"


class DeviceStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    error = "error"


class Device(UUIDMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "devices"

    type: Mapped[DeviceType] = mapped_column(Enum(DeviceType, name="device_type"))
    name: Mapped[str] = mapped_column(String(255))
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mac: Mapped[str | None] = mapped_column(String(64), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus, name="device_status"), default=DeviceStatus.offline
    )
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
