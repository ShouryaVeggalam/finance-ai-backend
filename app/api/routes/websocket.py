from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["WebSockets"])

_connections: dict[str, list[WebSocket]] = {}


@router.websocket("/ws/alerts/{company_id}")
async def alerts_websocket(websocket: WebSocket, company_id: str):
    await websocket.accept()
    _connections.setdefault(company_id, []).append(websocket)
    logger.info("websocket_connected", company_id=company_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "ack", "message": f"Received: {data}"})
    except WebSocketDisconnect:
        _connections[company_id].remove(websocket)
        logger.info("websocket_disconnected", company_id=company_id)


async def broadcast_alert(company_id: str, alert: dict) -> None:
    for ws in _connections.get(company_id, []):
        try:
            await ws.send_json(alert)
        except Exception:
            pass
