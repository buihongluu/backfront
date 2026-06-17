"""Các kênh gửi thông báo. Email + Telegram chạy thật; Push + Loa là stub (Sprint sau)."""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


async def send_email(subject: str, body: str) -> None:
    if not settings.SMTP_HOST or not settings.EMAIL_TO:
        raise RuntimeError("SMTP/EMAIL_TO chưa cấu hình")

    def _send() -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = settings.EMAIL_TO
        msg.set_content(body)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
            server.send_message(msg)

    await asyncio.to_thread(_send)


async def send_telegram(text: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        raise RuntimeError("Telegram chưa cấu hình")
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            url, json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text}
        )
        resp.raise_for_status()


async def send_push(title: str, body: str) -> None:
    # TODO Sprint sau: tích hợp FCM
    logger.info("[PUSH stub] %s | %s", title, body)


async def send_speaker(title: str) -> None:
    # TODO Sprint sau: gọi loa cảnh báo (FEAT-RAD-05)
    logger.info("[LOA stub] phát cảnh báo: %s", title)
