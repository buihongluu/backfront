"""Validate RTSP nhẹ (không cần ffmpeg): mở TCP + gửi OPTIONS (FEAT-VMS-01)."""

import asyncio
from urllib.parse import urlparse


async def validate_rtsp(url: str, timeout: float = 5.0) -> tuple[bool, str]:
    parsed = urlparse(url)
    if parsed.scheme != "rtsp" or not parsed.hostname:
        return False, "URL không hợp lệ (phải bắt đầu bằng rtsp://)"

    host = parsed.hostname
    port = parsed.port or 554

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout
        )
    except asyncio.TimeoutError:
        return False, "Timeout — không kết nối được tới camera"
    except OSError:
        return False, "Không kết nối được (sai IP/cổng hoặc camera đang tắt)"

    try:
        request = f"OPTIONS {url} RTSP/1.0\r\nCSeq: 1\r\n\r\n"
        writer.write(request.encode())
        await writer.drain()
        data = await asyncio.wait_for(reader.read(1024), timeout)
        text = data.decode(errors="ignore")

        if not text.startswith("RTSP/"):
            return False, "Cổng mở nhưng không phải dịch vụ RTSP"
        if " 401" in text or " 403" in text:
            return False, "Sai thông tin đăng nhập (kiểm tra user/mật khẩu)"
        if " 200" in text or "RTSP/1.0" in text:
            return True, "OK"
        return True, "Camera phản hồi RTSP"
    except asyncio.TimeoutError:
        return False, "Camera không phản hồi RTSP"
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:  # noqa: BLE001
            pass
