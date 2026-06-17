"""Khai báo path camera vào MediaMTX qua Control API (FEAT-VMS-01/02)."""

import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


def path_name(camera_id) -> str:
    """Tên path trên MediaMTX (không dùng dấu '-')."""
    return f"cam{str(camera_id).replace('-', '')}"


async def add_path(name: str, source: str) -> None:
    """Thêm/cập nhật path đọc từ RTSP nguồn, phát on-demand."""
    body = {"source": source, "sourceOnDemand": True}
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            r = await client.post(
                f"{settings.MEDIAMTX_API}/v3/config/paths/add/{name}", json=body
            )
            if r.status_code >= 400:
                # đã tồn tại -> patch
                await client.patch(
                    f"{settings.MEDIAMTX_API}/v3/config/paths/patch/{name}", json=body
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("MediaMTX add_path(%s) lỗi: %s", name, exc)


async def remove_path(name: str) -> None:
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            await client.delete(f"{settings.MEDIAMTX_API}/v3/config/paths/delete/{name}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("MediaMTX remove_path(%s) lỗi: %s", name, exc)
