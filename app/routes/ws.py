from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..database import SessionLocal
from ..repositories.chats import ChatRepository
from ..ws.manager import manager


router = APIRouter()


def _websocket_user_id(websocket: WebSocket) -> int | None:
    raw_user_id = websocket.session.get("user_id")
    if raw_user_id is None:
        return None
    try:
        return int(raw_user_id)
    except (TypeError, ValueError):
        return None


def _user_can_open_chat(*, chat_id: int, user_id: int) -> bool:
    db = SessionLocal()
    try:
        return ChatRepository(db).user_in_chat(chat_id=chat_id, user_id=user_id)
    finally:
        db.close()


@router.websocket("/ws/chat/{chat_id}")
async def chat_ws(chat_id: int, websocket: WebSocket):
    user_id = _websocket_user_id(websocket)
    if user_id is None or not _user_can_open_chat(chat_id=chat_id, user_id=user_id):
        await websocket.close(code=1008)
        return

    await manager.connect_chat(chat_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_chat(chat_id, websocket)


@router.websocket("/ws/notifications/{user_id}")
async def notifications_ws(user_id: int, websocket: WebSocket):
    current_user_id = _websocket_user_id(websocket)
    if current_user_id != user_id:
        await websocket.close(code=1008)
        return

    await manager.connect_notifications(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_notifications(user_id, websocket)
