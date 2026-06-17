import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.models import UserRole
from apps.devices.models import Device, DeviceStatus, DeviceType
from apps.devices.schemas import DeviceCreate, DeviceOut, DeviceUpdate
from core.config import settings
from core.database import get_session
from core.deps import get_current_user, require_roles
from core.realtime import manager

router = APIRouter(prefix="/devices", tags=["devices"])

staff_only = Depends(require_roles(UserRole.admin, UserRole.operator))


async def _broadcast_status(device: Device) -> None:
    await manager.broadcast(
        {
            "type": "device_status",
            "device_id": str(device.id),
            "name": device.name,
            "status": device.status.value,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        }
    )


@router.get("", response_model=list[DeviceOut], dependencies=[Depends(get_current_user)])
async def list_devices(
    db: AsyncSession = Depends(get_session),
    type: DeviceType | None = None,
    status_: DeviceStatus | None = Query(None, alias="status"),
):
    stmt = select(Device).order_by(Device.created_at.desc())
    if type is not None:
        stmt = stmt.where(Device.type == type)
    if status_ is not None:
        stmt = stmt.where(Device.status == status_)
    rows = (await db.scalars(stmt)).all()
    return [DeviceOut.model_validate(d) for d in rows]


@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED, dependencies=[staff_only])
async def create_device(body: DeviceCreate, db: AsyncSession = Depends(get_session)):
    device = Device(
        tenant_id=uuid.UUID(settings.DEFAULT_TENANT_ID),
        type=body.type,
        name=body.name,
        ip=body.ip,
        mac=body.mac,
        location=body.location,
        status=DeviceStatus.offline,
        meta=body.meta or {},
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return DeviceOut.model_validate(device)


@router.get("/{device_id}", response_model=DeviceOut, dependencies=[Depends(get_current_user)])
async def get_device(device_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    device = await db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị")
    return DeviceOut.model_validate(device)


@router.patch("/{device_id}", response_model=DeviceOut, dependencies=[staff_only])
async def update_device(
    device_id: uuid.UUID, body: DeviceUpdate, db: AsyncSession = Depends(get_session)
):
    device = await db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị")

    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(device, field, value)
    await db.commit()
    await db.refresh(device)
    await _broadcast_status(device)
    return DeviceOut.model_validate(device)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_roles(UserRole.admin))])
async def delete_device(device_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    device = await db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị")
    await db.delete(device)
    await db.commit()


@router.post("/{device_id}/heartbeat", response_model=DeviceOut)
async def heartbeat(device_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    """Thiết bị/worker gọi định kỳ -> online + cập nhật last_seen (FEAT-CORE-03)."""
    device = await db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị")
    device.last_seen = datetime.now(timezone.utc)
    if device.status != DeviceStatus.online:
        device.status = DeviceStatus.online
    await db.commit()
    await db.refresh(device)
    await _broadcast_status(device)
    return DeviceOut.model_validate(device)
