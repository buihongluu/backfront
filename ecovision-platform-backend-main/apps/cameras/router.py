import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.models import UserRole
from apps.cameras import mediamtx
from apps.cameras.models import Camera
from apps.cameras.rtsp import validate_rtsp
from apps.cameras.schemas import (
    CameraCreate,
    CameraOut,
    CameraUpdate,
    StreamUrls,
    ValidateRequest,
    ValidateResult,
)
from core.config import settings
from core.database import get_session
from core.deps import get_current_user, require_roles

router = APIRouter(prefix="/cameras", tags=["cameras"])

staff_only = Depends(require_roles(UserRole.admin, UserRole.operator))


@router.post("/validate", response_model=ValidateResult, dependencies=[staff_only])
async def validate(body: ValidateRequest):
    ok, reason = await validate_rtsp(body.rtsp_url)
    return ValidateResult(ok=ok, reason=reason)


@router.get("", response_model=list[CameraOut], dependencies=[Depends(get_current_user)])
async def list_cameras(db: AsyncSession = Depends(get_session)):
    rows = (await db.scalars(select(Camera).order_by(Camera.created_at.desc()))).all()
    return [CameraOut.model_validate(c) for c in rows]


@router.get("/internal/ai-enabled")
async def ai_enabled_cameras(db: AsyncSession = Depends(get_session)):
    """Nội bộ (dev, không auth): ai_worker lấy camera bật AI để chấm công."""
    rows = (
        await db.scalars(
            select(Camera).where(Camera.enabled.is_(True), Camera.ai_enabled.is_(True))
        )
    ).all()
    return [{"id": str(c.id), "rtsp_url": c.rtsp_url} for c in rows]


@router.get("/internal/rtsp/{camera_id}")
async def internal_rtsp(camera_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    """Nội bộ (dev): ai_worker lấy RTSP theo id để chụp snapshot."""
    cam = await db.get(Camera, camera_id)
    if cam is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy camera")
    return {"rtsp_url": cam.rtsp_url}


@router.post("", response_model=CameraOut, status_code=status.HTTP_201_CREATED, dependencies=[staff_only])
async def create_camera(body: CameraCreate, db: AsyncSession = Depends(get_session)):
    # R3: bắt buộc validate thành công mới lưu
    ok, reason = await validate_rtsp(body.rtsp_url)
    if not ok:
        raise HTTPException(status_code=400, detail=f"RTSP không hợp lệ: {reason}")

    camera = Camera(
        tenant_id=uuid.UUID(settings.DEFAULT_TENANT_ID),
        name=body.name,
        rtsp_url=body.rtsp_url,
        location=body.location,
        ai_enabled=body.ai_enabled,
        analyze_fps=body.analyze_fps,
    )
    db.add(camera)
    await db.commit()
    await db.refresh(camera)

    await mediamtx.add_path(mediamtx.path_name(camera.id), camera.rtsp_url)
    return CameraOut.model_validate(camera)


@router.get("/{camera_id}", response_model=CameraOut, dependencies=[Depends(get_current_user)])
async def get_camera(camera_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    camera = await db.get(Camera, camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy camera")
    return CameraOut.model_validate(camera)


@router.patch("/{camera_id}", response_model=CameraOut, dependencies=[staff_only])
async def update_camera(
    camera_id: uuid.UUID, body: CameraUpdate, db: AsyncSession = Depends(get_session)
):
    camera = await db.get(Camera, camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy camera")

    data = body.model_dump(exclude_unset=True)
    if "rtsp_url" in data and data["rtsp_url"] != camera.rtsp_url:
        ok, reason = await validate_rtsp(data["rtsp_url"])
        if not ok:
            raise HTTPException(status_code=400, detail=f"RTSP không hợp lệ: {reason}")

    for field, value in data.items():
        setattr(camera, field, value)
    await db.commit()
    await db.refresh(camera)

    await mediamtx.add_path(mediamtx.path_name(camera.id), camera.rtsp_url)
    return CameraOut.model_validate(camera)


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[staff_only])
async def delete_camera(camera_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    camera = await db.get(Camera, camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy camera")
    await mediamtx.remove_path(mediamtx.path_name(camera.id))
    await db.delete(camera)
    await db.commit()


@router.get("/{camera_id}/stream", response_model=StreamUrls, dependencies=[Depends(get_current_user)])
async def stream_urls(camera_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    camera = await db.get(Camera, camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy camera")
    name = mediamtx.path_name(camera.id)
    # đảm bảo path tồn tại trên MediaMTX (idempotent) -> tự lành nếu trước đó đăng ký lỗi
    await mediamtx.add_path(name, camera.rtsp_url)
    return StreamUrls(
        path=name,
        webrtc=f"{settings.MEDIAMTX_WEBRTC}/{name}",
        hls=f"{settings.MEDIAMTX_HLS}/{name}/index.m3u8",
    )
