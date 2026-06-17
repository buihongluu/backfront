"""Event Bus (FEAT-CORE-04): subscribe MQTT, biến detection thành Alert.

- Lưu ring buffer message gần nhất để trang giám sát đọc.
- Map topic detection -> tạo Alert qua alerts.service.
"""

import asyncio
import json
import logging
import time
from collections import deque

import aiomqtt

from apps.alerts.models import AlertLevel
from apps.alerts.service import create_alert
from apps.attendance.service import create_attendance
from core.config import settings
from core.database import SessionLocal
from core.realtime import manager

logger = logging.getLogger(__name__)

recent_messages: deque = deque(maxlen=500)
_state = {"connected": False}

# event (phần cuối topic) -> (kind, level)
TOPIC_MAP: dict[str, tuple[str, AlertLevel]] = {
    "person_detected": ("person", AlertLevel.warning),
    "fire_detected": ("fire", AlertLevel.critical),
    "smoke_detected": ("smoke", AlertLevel.critical),
    "ppe_violation": ("ppe", AlertLevel.warning),
    "stroke_detected": ("stroke", AlertLevel.critical),
    "fall_detected": ("fall", AlertLevel.critical),
}


def broker_connected() -> bool:
    return _state["connected"]


def _topics() -> list[str]:
    return [t.strip() for t in settings.EVENT_TOPICS.split(",") if t.strip()]


async def _handle(topic: str, raw: bytes) -> None:
    try:
        data = json.loads(raw)
    except Exception:  # noqa: BLE001
        data = {"raw": raw.decode(errors="ignore")[:200]}

    recent_messages.appendleft({"ts": time.time(), "topic": topic, "payload": data})

    # Stream box khuôn mặt realtime (không lưu DB) — chỉ broadcast để vẽ
    if topic == "attendance/faces":
        await manager.broadcast({"type": "faces", **data})
        return

    # Chấm công khuôn mặt (FEAT-ATT-03) từ ai_worker
    if topic == "attendance/checkin":
        async with SessionLocal() as db:
            await create_attendance(db, data)
        return

    parts = topic.split("/")
    if len(parts) < 3:
        return
    source_type, source_id, event = parts[0], parts[1], parts[2]
    mapping = TOPIC_MAP.get(event)
    if mapping is None:
        return

    kind, level = mapping
    async with SessionLocal() as db:
        await create_alert(
            db,
            source_type=source_type,
            source_id=source_id,
            kind=kind,
            level=level,
            payload=data,
            image_url=data.get("image_url"),
        )


async def start_event_subscriber() -> None:
    """Vòng lặp subscribe MQTT, tự kết nối lại khi lỗi."""
    while True:
        try:
            async with aiomqtt.Client(
                hostname=settings.MQTT_HOST,
                port=settings.MQTT_PORT,
                username=settings.MQTT_USERNAME or None,
                password=settings.MQTT_PASSWORD or None,
            ) as client:
                _state["connected"] = True
                topics = _topics() + ["attendance/checkin", "attendance/faces"]
                logger.info("Event subscriber đã kết nối, topics=%s", topics)
                for topic in topics:
                    await client.subscribe(topic)
                async for message in client.messages:
                    await _handle(str(message.topic), message.payload)
        except Exception as exc:  # noqa: BLE001
            _state["connected"] = False
            logger.warning("Event subscriber lỗi (%s) — thử lại sau 5s", exc)
            await asyncio.sleep(5)
