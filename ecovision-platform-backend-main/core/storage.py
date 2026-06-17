import logging

from minio import Minio

from core.config import settings

logger = logging.getLogger(__name__)

minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)


def ensure_bucket() -> None:
    """Tạo bucket mặc định nếu chưa có (gọi lúc startup). Sync — chạy trong thread."""
    try:
        if not minio_client.bucket_exists(settings.MINIO_BUCKET):
            minio_client.make_bucket(settings.MINIO_BUCKET)
            logger.info("Đã tạo bucket MinIO: %s", settings.MINIO_BUCKET)
    except Exception as exc:  # noqa: BLE001
        logger.warning("MinIO chưa sẵn sàng (%s)", exc)
