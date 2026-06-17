import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.attendance import service
from apps.attendance.models import Attendance, Shift
from apps.attendance.schemas import (
    AttendanceOut,
    ReportResponse,
    ShiftCreate,
    ShiftOut,
    ShiftUpdate,
)
from apps.auth.models import UserRole
from core.config import settings
from core.database import get_session
from core.deps import get_current_user, require_roles

router = APIRouter(prefix="/attendance", tags=["attendance"])

staff_only = Depends(require_roles(UserRole.admin, UserRole.operator))


@router.get("", response_model=list[AttendanceOut], dependencies=[Depends(get_current_user)])
async def list_attendance(
    db: AsyncSession = Depends(get_session),
    since: datetime | None = None,
    limit: int = 100,
):
    stmt = select(Attendance).order_by(Attendance.created_at.desc()).limit(limit)
    if since is not None:
        stmt = stmt.where(Attendance.created_at >= since)
    rows = (await db.scalars(stmt)).all()
    return [AttendanceOut.model_validate(a) for a in rows]


@router.get("/report", response_model=ReportResponse, dependencies=[Depends(get_current_user)])
async def report(
    db: AsyncSession = Depends(get_session),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    shift_id: uuid.UUID | None = None,
):
    return await service.build_report(db, date_from, date_to, shift_id)


# ---- Shifts ----
@router.get("/shifts", response_model=list[ShiftOut], dependencies=[Depends(get_current_user)])
async def list_shifts(db: AsyncSession = Depends(get_session)):
    rows = (await db.scalars(select(Shift).order_by(Shift.created_at))).all()
    return [ShiftOut.model_validate(s) for s in rows]


@router.post("/shifts", response_model=ShiftOut, status_code=status.HTTP_201_CREATED, dependencies=[staff_only])
async def create_shift(body: ShiftCreate, db: AsyncSession = Depends(get_session)):
    shift = Shift(tenant_id=uuid.UUID(settings.DEFAULT_TENANT_ID), **body.model_dump())
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    return ShiftOut.model_validate(shift)


@router.patch("/shifts/{shift_id}", response_model=ShiftOut, dependencies=[staff_only])
async def update_shift(shift_id: uuid.UUID, body: ShiftUpdate, db: AsyncSession = Depends(get_session)):
    shift = await db.get(Shift, shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy ca")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(shift, k, v)
    await db.commit()
    await db.refresh(shift)
    return ShiftOut.model_validate(shift)


@router.delete("/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[staff_only])
async def delete_shift(shift_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    shift = await db.get(Shift, shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy ca")
    await db.delete(shift)
    await db.commit()
