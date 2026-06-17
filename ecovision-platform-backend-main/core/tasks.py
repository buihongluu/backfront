"""Tác vụ nền: tự chuyển thiết bị sang offline khi quá hạn heartbeat (FEAT-CORE-03 R6)."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from apps.devices.models import Device, DeviceStatus
from core.config import settings
from core.database import SessionLocal
from core.realtime import manager

logger = logging.getLogger(__name__)


async def device_offline_sweeper() -> None:
    while True:
        await asyncio.sleep(settings.DEVICE_OFFLINE_TIMEOUT)
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=settings.DEVICE_OFFLINE_TIMEOUT
        )
        async with SessionLocal() as db:
            stale = (
                await db.scalars(
                    select(Device).where(
                        Device.status == DeviceStatus.online,
                        Device.last_seen < cutoff,
                    )
                )
            ).all()
            if not stale:
                continue
            for device in stale:
                device.status = DeviceStatus.offline
            await db.commit()
            for device in stale:
                await manager.broadcast(
                    {
                        "type": "device_status",
                        "device_id": str(device.id),
                        "name": device.name,
                        "status": "offline",
                        "last_seen": device.last_seen.isoformat()
                        if device.last_seen
                        else None,
                    }
                )
            logger.info("Đã chuyển %d thiết bị sang offline", len(stale))
