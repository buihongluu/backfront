"""Seed dữ liệu khởi tạo: tenant mặc định + tài khoản admin.

Chạy: docker compose exec backend python scripts/seed.py
"""

import asyncio
import os
import sys
import uuid

# cho phép chạy trực tiếp `python scripts/seed.py`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select  # noqa: E402

from core.config import settings
from core.database import Base, SessionLocal, engine
from core.security import hash_password
from apps.auth.models import User, UserRole

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # đổi sau khi đăng nhập lần đầu


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        existing = await session.scalar(
            select(User).where(User.username == ADMIN_USERNAME)
        )
        if existing:
            print(f"Tài khoản '{ADMIN_USERNAME}' đã tồn tại — bỏ qua.")
            return

        user = User(
            tenant_id=uuid.UUID(settings.DEFAULT_TENANT_ID),
            username=ADMIN_USERNAME,
            full_name="Administrator",
            hashed_password=hash_password(ADMIN_PASSWORD),
            role=UserRole.admin,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"Đã tạo admin: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
