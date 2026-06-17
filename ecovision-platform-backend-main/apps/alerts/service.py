import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from apps.alerts.models import Alert, AlertLevel, AlertStatus
from apps.alerts.schemas import AlertOut
from apps.auth.models import User
from apps.notifications.service import dispatch_alert
from core.config import settings
from core.realtime import manager
from core.redis_client import redis_client


async def create_alert(
    db: AsyncSession,
    *,
    source_type: str,
    kind: str,
    level: AlertLevel,
    source_id: str | None = None,
    payload: dict | None = None,
    image_url: str | None = None,
    clip_url: str | None = None,
) -> Alert | None:
    """Tạo alert (có dedup), broadcast realtime + fan-out notification.

    Trả None nếu bị dedup (cùng nguồn/kind/level trong ALERT_DEDUP_SECONDS).
    """
    dedup_key = f"alertdedup:{source_id}:{kind}:{level.value}"
    created = await redis_client.set(
        dedup_key, "1", nx=True, ex=settings.ALERT_DEDUP_SECONDS
    )
    if not created:
        return None

    alert = Alert(
        tenant_id=uuid.UUID(settings.DEFAULT_TENANT_ID),
        source_type=source_type,
        source_id=source_id,
        kind=kind,
        level=level,
        payload=payload or {},
        image_url=image_url,
        clip_url=clip_url,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    data = AlertOut.model_validate(alert).model_dump(mode="json")
    await manager.broadcast({"type": "alert", "alert": data})
    await dispatch_alert(db, alert)
    return alert


async def ack_alert(db: AsyncSession, alert: Alert, user: User) -> Alert:
    # R3: chỉ new -> ack
    if alert.status != AlertStatus.new:
        raise ValueError("Chỉ ack được alert ở trạng thái new")
    alert.status = AlertStatus.ack
    alert.acked_by = user.id
    alert.acked_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(alert)
    return alert


async def resolve_alert(db: AsyncSession, alert: Alert, user: User) -> Alert:
    # R3: không lùi từ resolved
    if alert.status == AlertStatus.resolved:
        raise ValueError("Alert đã resolved")
    alert.status = AlertStatus.resolved
    alert.resolved_at = datetime.now(timezone.utc)
    if alert.acked_by is None:
        alert.acked_by = user.id
    await db.commit()
    await db.refresh(alert)
    return alert
