from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Notification


class NotificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_user(self, user_id: int, limit: int = 10) -> list[Notification]:
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(query))

    def create(self, *, user_id: int, kind: str, content: str) -> Notification:
        notification = Notification(user_id=user_id, kind=kind, content=content)
        self.session.add(notification)
        self.session.flush()
        return notification
