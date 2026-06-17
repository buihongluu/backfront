import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from apps.devices.models import DeviceStatus


class CameraCreate(BaseModel):
    name: str
    rtsp_url: str
    location: str | None = None
    cluster: str | None = None
    ai_enabled: bool = False
    analyze_fps: int = 3


class CameraUpdate(BaseModel):
    name: str | None = None
    rtsp_url: str | None = None
    location: str | None = None
    cluster: str | None = None
    enabled: bool | None = None
    ai_enabled: bool | None = None
    analyze_fps: int | None = None


class CameraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    rtsp_url: str
    location: str | None
    cluster: str | None
    enabled: bool
    ai_enabled: bool
    analyze_fps: int
    status: DeviceStatus
    last_seen: datetime | None
    created_at: datetime


class ValidateRequest(BaseModel):
    rtsp_url: str


class ValidateResult(BaseModel):
    ok: bool
    reason: str


class StreamUrls(BaseModel):
    path: str
    webrtc: str
    hls: str
