import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.models import User, UserRole
from apps.auth.schemas import PasswordReset, UserCreate, UserOut, UserUpdate
from core.config import settings
from core.database import get_session
from core.deps import get_current_user, require_roles
from core.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])

# Mọi route yêu cầu quyền admin (FEAT-CORE-02 R1)
admin_only = Depends(require_roles(UserRole.admin))


async def _count_active_admins(db: AsyncSession) -> int:
    return await db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.role == UserRole.admin, User.is_active.is_(True))
    )


@router.get("", response_model=list[UserOut], dependencies=[admin_only])
async def list_users(
    db: AsyncSession = Depends(get_session),
    role: UserRole | None = None,
    search: str | None = None,
):
    stmt = select(User).order_by(User.created_at.desc())
    if role is not None:
        stmt = stmt.where(User.role == role)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(User.username.ilike(like), User.full_name.ilike(like)))
    rows = (await db.scalars(stmt)).all()
    return [UserOut.model_validate(u) for u in rows]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[admin_only])
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_session)):
    exists = await db.scalar(select(User).where(User.username == body.username))
    if exists:
        raise HTTPException(status_code=409, detail="Username đã tồn tại")

    user = User(
        tenant_id=uuid.UUID(settings.DEFAULT_TENANT_ID),
        username=body.username,
        full_name=body.full_name,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/{user_id}", response_model=UserOut, dependencies=[admin_only])
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_session),
    current: User = Depends(require_roles(UserRole.admin)),
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    # R4: không tự khóa mình
    if body.is_active is False and user.id == current.id:
        raise HTTPException(status_code=400, detail="Không thể tự khóa tài khoản của mình")

    # R4: không khóa / hạ quyền admin active cuối cùng
    losing_admin = user.role == UserRole.admin and user.is_active and (
        body.is_active is False
        or (body.role is not None and body.role != UserRole.admin)
    )
    if losing_admin and await _count_active_admins(db) <= 1:
        raise HTTPException(status_code=400, detail="Phải còn ít nhất 1 admin đang hoạt động")

    if body.full_name is not None:
        user.full_name = body.full_name
    if body.email is not None:
        user.email = body.email
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT, dependencies=[admin_only])
async def reset_password(
    user_id: uuid.UUID, body: PasswordReset, db: AsyncSession = Depends(get_session)
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    user.hashed_password = hash_password(body.new_password)
    await db.commit()
