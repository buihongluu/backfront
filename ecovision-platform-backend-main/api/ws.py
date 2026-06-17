from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from core.realtime import manager
from core.security import decode_token

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(...)):
    """Realtime CMS. Xác thực bằng access token qua query param ?token=..."""
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("wrong token type")
    except Exception:  # noqa: BLE001
        await ws.close(code=1008)
        return

    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # giữ kết nối; client có thể gửi ping
    except WebSocketDisconnect:
        manager.disconnect(ws)
