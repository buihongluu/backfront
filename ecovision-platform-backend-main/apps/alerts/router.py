import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.alerts import service
from apps.alerts.models import Alert, AlertLevel, AlertStatus
from apps.alerts.schemas import AlertCreate, AlertOut
from apps.auth.models import User, UserRole
from core.database import get_session
from core.deps import get_current_user, require_roles

router = APIRouter(prefix="/alerts", tags=["alerts"])

staff_only = Depends(require_roles(UserRole.admin, UserRole.operator))


@router.get("", response_model=list[AlertOut], dependencies=[Depends(get_current_user)])
async def list_alerts(
    db: AsyncSession = Depends(get_session),
    level: AlertLevel | None = None,
    status_: AlertStatus | None = Query(None, alias="status"),
    source_type: str | None = None,
    since: datetime | None = None,
    limit: int = 100,
):
    stmt = select(Alert).order_by(Alert.created_at.desc()).limit(limit)
    if level is not None:
        stmt = stmt.where(Alert.level == level)
    if status_ is not None:
        stmt = stmt.where(Alert.status == status_)
    if source_type is not None:
        stmt = stmt.where(Alert.source_type == source_type)
    if since is not None:
        stmt = stmt.where(Alert.created_at >= since)
    rows = (await db.scalars(stmt)).all()
    return [AlertOut.model_validate(a) for a in rows]


@router.get("/unread-count", dependencies=[Depends(get_current_user)])
async def unread_count(db: AsyncSession = Depends(get_session)):
    """Badge: số alert trạng thái new (FEAT-CORE-05 R8)."""
    count = await db.scalar(
        select(func.count()).select_from(Alert).where(Alert.status == AlertStatus.new)
    )
    return {"count": count or 0}


@router.post("", response_model=AlertOut, status_code=status.HTTP_201_CREATED, dependencies=[staff_only])
async def create_alert(body: AlertCreate, db: AsyncSession = Depends(get_session)):
    alert = await service.create_alert(
        db,
        source_type=body.source_type,
        source_id=body.source_id,
        kind=body.kind,
        level=body.level,
        payload=body.payload,
        image_url=body.image_url,
        clip_url=body.clip_url,
    )
    if alert is None:
        raise HTTPException(status_code=429, detail="Bị dedup (trùng sự kiện gần đây)")
    return AlertOut.model_validate(alert)


@router.get("/{alert_id}", response_model=AlertOut, dependencies=[Depends(get_current_user)])
async def get_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy alert")
    return AlertOut.model_validate(alert)


@router.post("/{alert_id}/ack", response_model=AlertOut)
async def ack(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(require_roles(UserRole.admin, UserRole.operator)),
):
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy alert")
    try:
        alert = await service.ack_alert(db, alert, user)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AlertOut.model_validate(alert)


@router.post("/{alert_id}/resolve", response_model=AlertOut)
async def resolve(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(require_roles(UserRole.admin, UserRole.operator)),
):
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy alert")
    try:
        alert = await service.resolve_alert(db, alert, user)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AlertOut.model_validate(alert)
