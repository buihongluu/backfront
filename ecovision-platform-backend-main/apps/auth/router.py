import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.models import User
from apps.auth.schemas import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserOut,
)
from core.config import settings
from core.database import get_session
from core.deps import get_current_user
from core.redis_client import redis_client
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _revoked_key(jti: str) -> str:
    return f"revoked:{jti}"


def _fail_key(username: str) -> str:
    return f"loginfail:{username.lower()}"


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_session)):
    # Throttle: quá số lần sai -> khóa tạm (FEAT-CORE-01 R3)
    fails = await redis_client.get(_fail_key(body.username))
    if fails is not None and int(fails) >= settings.LOGIN_MAX_FAILS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Đăng nhập sai quá nhiều lần, thử lại sau {settings.LOGIN_LOCK_SECONDS}s",
        )

    user = await db.scalar(select(User).where(User.username == body.username))
    # R2: không phân biệt sai user hay sai mật khẩu
    if user is None or not verify_password(body.password, user.hashed_password):
        async with redis_client.pipeline() as pipe:
            pipe.incr(_fail_key(body.username))
            pipe.expire(_fail_key(body.username), settings.LOGIN_LOCK_SECONDS)
            await pipe.execute()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tài khoản hoặc mật khẩu",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị khóa"
        )

    await redis_client.delete(_fail_key(body.username))
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id, user.role.value),
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_session)):
    try:
        payload = decode_token(body.refresh_token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Refresh token không hợp lệ") from exc

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Sai loại token")

    if await redis_client.get(_revoked_key(payload.get("jti", ""))):
        raise HTTPException(status_code=401, detail="Token đã thu hồi")

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Tài khoản không hợp lệ")

    return AccessTokenResponse(access_token=create_access_token(user.id, user.role.value))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest):
    """Thu hồi refresh token (đưa jti vào blocklist tới khi hết hạn)."""
    try:
        payload = decode_token(body.refresh_token)
    except Exception:  # noqa: BLE001
        return  # token rác -> coi như đã logout
    jti = payload.get("jti")
    if jti:
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await redis_client.set(_revoked_key(jti), "1", ex=ttl)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
