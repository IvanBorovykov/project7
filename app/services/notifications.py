from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import Notification
from ..repositories.notifications import NotificationRepository


class NotificationService:
    def __init__(self, session: Session) -> None:
        self.notifications = NotificationRepository(session)

    def list_for_user(self, user_id: int, limit: int = 10) -> list[Notification]:
        return self.notifications.list_for_user(user_id, limit=limit)

    def create(self, *, user_id: int, kind: str, content: str) -> Notification:
        return self.notifications.create(user_id=user_id, kind=kind, content=content)
