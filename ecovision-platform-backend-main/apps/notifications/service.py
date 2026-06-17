"""Định tuyến + gửi thông báo theo mức alert (FEAT-CORE-06)."""

import json
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from apps.alerts.models import Alert, AlertLevel
from apps.notifications import channels
from apps.notifications.models import NotificationLog
from core.config import settings

logger = logging.getLogger(__name__)

# Định tuyến theo mức (in-app luôn có nhờ WebSocket; đây là kênh ngoài)
ROUTES: dict[AlertLevel, list[str]] = {
    AlertLevel.critical: ["email", "telegram", "push", "speaker"],
    AlertLevel.warning: ["email", "push"],
    AlertLevel.info: [],
}


async def _send_one(
    db: AsyncSession, alert: Alert | None, channel: str, title: str, body: str
) -> None:
    status, error = "sent", None
    try:
        if channel == "email":
            await channels.send_email(title, body)
        elif channel == "telegram":
            await channels.send_telegram(f"{title}\n{body}")
        elif channel == "push":
            await channels.send_push(title, body)
        elif channel == "speaker":
            await channels.send_speaker(title)
        else:
            raise RuntimeError(f"Kênh không hỗ trợ: {channel}")
    except Exception as exc:  # noqa: BLE001
        status, error = "failed", str(exc)[:500]
        logger.warning("Gửi %s thất bại: %s", channel, exc)

    db.add(
        NotificationLog(
            tenant_id=uuid.UUID(settings.DEFAULT_TENANT_ID),
            channel=channel,
            level=(alert.level.value if alert else "info"),
            title=title[:255],
            status=status,
            error=error,
            alert_id=alert.id if alert else None,
        )
    )
    await db.commit()


async def dispatch_alert(db: AsyncSession, alert: Alert) -> None:
    title = f"[{alert.level.value.upper()}] {alert.kind} @ {alert.source_id or alert.source_type}"
    body = json.dumps(alert.payload, ensure_ascii=False) if alert.payload else title
    for channel in ROUTES.get(alert.level, []):
        await _send_one(db, alert, channel, title, body)


async def send_test(db: AsyncSession, channel: str) -> None:
    await _send_one(db, None, channel, "[TEST] EcoVision", "Tin nhắn thử nghiệm")
