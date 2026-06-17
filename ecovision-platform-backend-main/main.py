import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import Base, engine
from core.events import start_event_subscriber
from core.logging import setup_logging
from core.mqtt import mqtt_client
from core.redis_client import redis_client
from core.storage import ensure_bucket
from core.tasks import device_offline_sweeper

# import models để metadata được nạp (create_all / Alembic)
from apps.auth import models as _auth_models  # noqa: F401
from apps.devices import models as _device_models  # noqa: F401
from apps.cameras import models as _camera_models  # noqa: F401
from apps.alerts import models as _alert_models  # noqa: F401
from apps.attendance import models as _att_models  # noqa: F401
from apps.notifications import models as _notif_models  # noqa: F401

# routers
from api.health import router as health_router
from api.events import router as events_router
from api.ws import router as ws_router
from apps.auth.router import router as auth_router
from apps.auth.users import router as users_router
from apps.devices.router import router as devices_router
from apps.cameras.router import router as cameras_router
from apps.alerts.router import router as alerts_router
from apps.attendance.router import router as attendance_router
from apps.notifications.router import router as notifications_router

setup_logging()
logger = logging.getLogger("ecovision")

_background: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Khởi động %s (env=%s)", settings.APP_NAME, settings.ENV)

    if settings.CREATE_TABLES_ON_STARTUP:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Đã đảm bảo schema (create_all)")

    await asyncio.to_thread(ensure_bucket)
    await mqtt_client.start()

    _background.append(asyncio.create_task(start_event_subscriber()))
    _background.append(asyncio.create_task(device_offline_sweeper()))

    yield

    for task in _background:
        task.cancel()
    await mqtt_client.stop()
    await redis_client.aclose()
    await engine.dispose()
    logger.info("Đã dừng %s", settings.APP_NAME)


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(devices_router)
app.include_router(cameras_router)
app.include_router(alerts_router)
app.include_router(attendance_router)
app.include_router(notifications_router)
app.include_router(events_router)
app.include_router(ws_router)


@app.get("/", tags=["root"])
async def root() -> dict:
    return {"name": settings.APP_NAME, "docs": "/docs", "health": "/health"}
