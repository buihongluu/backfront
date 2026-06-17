from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình đọc từ biến môi trường (docker-compose nạp từ .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "EcoVision Platform"
    ENV: str = "dev"
    DEBUG: bool = True
    CREATE_TABLES_ON_STARTUP: bool = True

    # PostgreSQL
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "ecovision"
    POSTGRES_PASSWORD: str = "ecovision"
    POSTGRES_DB: str = "ecovision"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # MQTT (broker external)
    MQTT_HOST: str = "host.docker.internal"
    MQTT_PORT: int = 1883
    MQTT_USERNAME: str | None = None
    MQTT_PASSWORD: str | None = None

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "ecovision"

    # Media server
    MEDIAMTX_API: str = "http://mediamtx:9997"
    MEDIAMTX_WEBRTC: str = "http://localhost:8889"
    MEDIAMTX_HLS: str = "http://localhost:8888"

    # Auth
    JWT_SECRET: str = "change-me-please-32chars-minimum-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Single-tenant
    DEFAULT_TENANT_ID: str = "00000000-0000-0000-0000-000000000001"

    # Auth throttle (FEAT-CORE-01 R3)
    LOGIN_MAX_FAILS: int = 5
    LOGIN_LOCK_SECONDS: int = 30

    # Device (FEAT-CORE-03)
    DEVICE_OFFLINE_TIMEOUT: int = 60  # giây không heartbeat -> offline

    # Alert / Notification
    ALERT_DEDUP_SECONDS: int = 30  # chống spam cùng sự kiện
    EVENT_TOPICS: str = "camera/#,radar/#"  # topic MQTT worker phát detection

    # Notification — Email (SMTP)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "ecovision@localhost"
    EMAIL_TO: str = ""  # danh sách email nhận, phân tách bằng dấu phẩy

    # Notification — Telegram
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
