import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.attendance.models import Attendance, Shift
from apps.attendance.schemas import AttendanceOut, ReportResponse, ReportRow
from core.config import settings
from core.realtime import manager


def _hhmm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


async def create_attendance(db: AsyncSession, data: dict) -> Attendance:
    att = Attendance(
        tenant_id=uuid.UUID(settings.DEFAULT_TENANT_ID),
        employee_code=str(data.get("employee_code", "")),
        name=str(data.get("name", "")),
        face_id=data.get("face_id"),
        camera_id=str(data.get("camera_id")) if data.get("camera_id") else None,
        type=str(data.get("type", "in")),
        score=float(data.get("score", 0) or 0),
        image_url=data.get("image_url"),
    )
    db.add(att)
    await db.commit()
    await db.refresh(att)

    msg = {
        "type": "attendance",
        "attendance": AttendanceOut.model_validate(att).model_dump(mode="json"),
    }
    # thông tin vẽ box (không lưu DB, chỉ realtime)
    for k in ("bbox", "frame_w", "frame_h"):
        if data.get(k) is not None:
            msg[k] = data[k]
    await manager.broadcast(msg)
    return att


async def build_report(
    db: AsyncSession,
    dt_from: datetime | None,
    dt_to: datetime | None,
    shift_id: uuid.UUID | None,
) -> ReportResponse:
    # chọn ca: theo id, hoặc ca active đầu tiên, hoặc mặc định 08:00-17:00
    shift = None
    if shift_id:
        shift = await db.get(Shift, shift_id)
    if shift is None:
        shift = await db.scalar(
            select(Shift).where(Shift.active.is_(True)).order_by(Shift.created_at)
        )
    start_min = _hhmm(shift.start_time) if shift else 8 * 60
    end_min = _hhmm(shift.end_time) if shift else 17 * 60
    grace = shift.grace_minutes if shift else 15

    stmt = select(Attendance)
    if dt_from:
        stmt = stmt.where(Attendance.created_at >= dt_from)
    if dt_to:
        stmt = stmt.where(Attendance.created_at <= dt_to)
    records = (await db.scalars(stmt)).all()

    # gom theo (nhân viên, ngày)
    days: dict[tuple, dict] = {}
    for a in records:
        key = (a.employee_code, a.created_at.date())
        d = days.setdefault(key, {"name": a.name, "times": []})
        d["times"].append(a.created_at)

    emp: dict[str, dict] = {}
    for (code, _day), info in days.items():
        times = sorted(info["times"])
        first, last = times[0], times[-1]
        e = emp.setdefault(code, {"name": info["name"], "work": 0, "late": 0, "early": 0, "hours": 0.0})
        e["work"] += 1
        if first.hour * 60 + first.minute > start_min + grace:
            e["late"] += 1
        if last.hour * 60 + last.minute < end_min:
            e["early"] += 1
        e["hours"] += max(0.0, (last - first).total_seconds()) / 3600

    rows = [
        ReportRow(
            employee_code=code,
            name=v["name"],
            work_days=v["work"],
            late=v["late"],
            early=v["early"],
            total_hours=round(v["hours"], 1),
        )
        for code, v in emp.items()
    ]
    metrics = {
        "employees": len(emp),
        "total_records": len(records),
        "late": sum(r.late for r in rows),
        "shift": shift.name if shift else "Mặc định 08:00-17:00",
    }
    return ReportResponse(metrics=metrics, rows=rows)
