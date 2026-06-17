"""Wrapper MQTT tối thiểu cho Sprint 1.

Broker là external (người dùng tự cung cấp). Nếu chưa kết nối được, publish sẽ
ghi log cảnh báo thay vì làm sập app — để hạ tầng khác vẫn chạy.
"""

import json
import logging

import aiomqtt

from core.config import settings

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self) -> None:
        self._client: aiomqtt.Client | None = None

    async def start(self) -> None:
        try:
            self._client = aiomqtt.Client(
                hostname=settings.MQTT_HOST,
                port=settings.MQTT_PORT,
                username=settings.MQTT_USERNAME or None,
                password=settings.MQTT_PASSWORD or None,
            )
            await self._client.__aenter__()
            logger.info("MQTT connected: %s:%s", settings.MQTT_HOST, settings.MQTT_PORT)
        except Exception as exc:  # noqa: BLE001
            logger.warning("MQTT connect failed (%s) — publish sẽ bị bỏ qua", exc)
            self._client = None

    async def stop(self) -> None:
        if self._client is not None:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass
            self._client = None

    @property
    def connected(self) -> bool:
        return self._client is not None

    async def publish(self, topic: str, payload: dict | str | bytes) -> None:
        if self._client is None:
            logger.warning("MQTT chưa kết nối — bỏ qua publish %s", topic)
            return
        data = payload if isinstance(payload, (str, bytes)) else json.dumps(payload)
        await self._client.publish(topic, data)


mqtt_client = MQTTClient()
