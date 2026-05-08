from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..ws.manager import manager


router = APIRouter()


@router.websocket("/ws/chat/{chat_id}")
async def chat_ws(chat_id: int, websocket: WebSocket):
    await manager.connect_chat(chat_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_chat(chat_id, websocket)


@router.websocket("/ws/notifications/{user_id}")
async def notifications_ws(user_id: int, websocket: WebSocket):
    await manager.connect_notifications(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_notifications(user_id, websocket)
