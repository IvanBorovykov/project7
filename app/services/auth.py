from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import User
from ..repositories.users import UserRepository


class AuthService:
    def __init__(self, session: Session) -> None:
        self.users = UserRepository(session)

    def login(self, username: str, password: str) -> User | None:
        user = self.users.get_by_username(username.strip())
        if user is None or user.password != password:
            return None
        return user
