from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.models import UserRole
from apps.notifications import service
from apps.notifications.models import NotificationLog
from apps.notifications.schemas import NotificationLogOut, TestRequest
from core.database import get_session
from core.deps import get_current_user, require_roles

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/routes", dependencies=[Depends(get_current_user)])
async def get_routes():
    """Định tuyến hiện tại theo mức alert."""
    return {level.value: chans for level, chans in service.ROUTES.items()}


@router.get("/logs", response_model=list[NotificationLogOut], dependencies=[Depends(get_current_user)])
async def list_logs(db: AsyncSession = Depends(get_session), limit: int = 100):
    rows = (
        await db.scalars(
            select(NotificationLog).order_by(NotificationLog.created_at.desc()).limit(limit)
        )
    ).all()
    return [NotificationLogOut.model_validate(r) for r in rows]


@router.post("/test", status_code=status.HTTP_202_ACCEPTED,
             dependencies=[Depends(require_roles(UserRole.admin))])
async def test_channel(body: TestRequest, db: AsyncSession = Depends(get_session)):
    await service.send_test(db, body.channel)
    return {"sent": body.channel}
