import asyncio

from fastapi import APIRouter
from sqlalchemy import text

from core.config import settings
from core.database import engine
from core.mqtt import mqtt_client
from core.redis_client import redis_client
from core.storage import minio_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": settings.APP_NAME, "env": settings.ENV}


@router.get("/health/deep")
async def health_deep() -> dict:
    checks: dict[str, str] = {}

    # PostgreSQL
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc}"

    # Redis
    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {exc}"

    # MinIO
    try:
        await asyncio.to_thread(minio_client.bucket_exists, settings.MINIO_BUCKET)
        checks["minio"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["minio"] = f"error: {exc}"

    # MQTT (external)
    checks["mqtt"] = "ok" if mqtt_client.connected else "disconnected"

    healthy = all(v == "ok" for k, v in checks.items() if k != "mqtt")
    return {"status": "ok" if healthy else "degraded", "checks": checks}
