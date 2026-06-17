from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import TenantMixin, TimestampMixin, UUIDMixin
from core.database import Base


class Shift(UUIDMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "shifts"

    name: Mapped[str] = mapped_column(String(128))
    start_time: Mapped[str] = mapped_column(String(5))  # "HH:MM"
    end_time: Mapped[str] = mapped_column(String(5))
    grace_minutes: Mapped[int] = mapped_column(Integer, default=15)
    applies_to: Mapped[str] = mapped_column(String(128), default="Toàn công ty")
    color: Mapped[str] = mapped_column(String(16), default="eco-green")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Attendance(UUIDMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "attendance"

    employee_code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    face_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    camera_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    type: Mapped[str] = mapped_column(String(8), default="in")  # in | out
    score: Mapped[float] = mapped_column(Float, default=0.0)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
