import ipaddress
import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from apps.devices.models import DeviceStatus, DeviceType

_MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$")


class DeviceBase(BaseModel):
    type: DeviceType
    name: str
    ip: str | None = None
    mac: str | None = None
    location: str | None = None
    meta: dict = {}

    @field_validator("ip")
    @classmethod
    def _check_ip(cls, v: str | None) -> str | None:
        if v:
            ipaddress.ip_address(v)  # raise nếu sai định dạng (R1)
        return v

    @field_validator("mac")
    @classmethod
    def _check_mac(cls, v: str | None) -> str | None:
        if v and not _MAC_RE.match(v):
            raise ValueError("MAC không đúng định dạng")
        return v


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: str | None = None
    ip: str | None = None
    mac: str | None = None
    location: str | None = None
    status: DeviceStatus | None = None
    meta: dict | None = None


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: DeviceType
    name: str
    ip: str | None
    mac: str | None
    location: str | None
    status: DeviceStatus
    last_seen: datetime | None
    meta: dict
    created_at: datetime
