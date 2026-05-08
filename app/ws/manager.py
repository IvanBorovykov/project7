from __future__ import annotations

from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.chat_connections: dict[int, list[WebSocket]] = defaultdict(list)
        self.notification_connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect_chat(self, chat_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.chat_connections[chat_id].append(websocket)

    async def connect_notifications(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.notification_connections[user_id].append(websocket)

    def disconnect_chat(self, chat_id: int, websocket: WebSocket) -> None:
        if websocket in self.chat_connections[chat_id]:
            self.chat_connections[chat_id].remove(websocket)

    def disconnect_notifications(self, user_id: int, websocket: WebSocket) -> None:
        if websocket in self.notification_connections[user_id]:
            self.notification_connections[user_id].remove(websocket)

    async def broadcast_chat(self, chat_id: int, payload: dict[str, str]) -> None:
        for websocket in list(self.chat_connections[chat_id]):
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect_chat(chat_id, websocket)

    async def notify_user(self, user_id: int, payload: dict[str, str]) -> None:
        for websocket in list(self.notification_connections[user_id]):
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect_notifications(user_id, websocket)


manager = ConnectionManager()
