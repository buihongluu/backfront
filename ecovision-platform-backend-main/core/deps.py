"""Dependencies dùng chung: lấy user hiện tại + kiểm tra quyền (RBAC)."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.models import User, UserRole
from core.database import get_session
from core.security import decode_token

bearer = HTTPBearer(auto_error=True)

_UNAUTH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token không hợp lệ hoặc đã hết hạn",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_session),
) -> User:
    try:
        payload = decode_token(creds.credentials)
    except Exception as exc:  # noqa: BLE001
        raise _UNAUTH from exc

    if payload.get("type") != "access":
        raise _UNAUTH

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise _UNAUTH from exc

    user = await db.get(User, user_id)
    # Khóa user / đổi trạng thái -> phiên mất hiệu lực ngay (FEAT-CORE-02 R5)
    if user is None or not user.is_active:
        raise _UNAUTH
    return user


def require_roles(*roles: UserRole):
    """Chặn truy cập nếu role hiện tại không nằm trong danh sách cho phép."""

    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không đủ quyền",
            )
        return user

    return checker
