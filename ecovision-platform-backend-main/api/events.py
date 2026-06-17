from fastapi import APIRouter, Depends

from apps.auth.models import UserRole
from core import events
from core.deps import require_roles

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/recent", dependencies=[Depends(require_roles(UserRole.admin))])
async def recent(limit: int = 100):
    """Giám sát Event Bus (chỉ admin) — message gần nhất + trạng thái broker."""
    return {
        "connected": events.broker_connected(),
        "messages": list(events.recent_messages)[:limit],
    }
