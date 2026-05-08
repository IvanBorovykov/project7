from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[User]:
        return list(self.session.scalars(select(User).order_by(User.full_name)))

    def get(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self.session.scalar(select(User).where(User.username == username))

    def create(self, *, username: str, password: str, full_name: str) -> User:
        user = User(username=username, password=password, full_name=full_name)
        self.session.add(user)
        self.session.flush()
        return user
