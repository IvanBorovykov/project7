from __future__ import annotations

from ..database import session_scope
from ..repositories.users import UserRepository
from .chats import ChatService


def seed_demo_data() -> None:
    with session_scope() as session:
        users = UserRepository(session)
        if users.get_by_username("alice") is None:
            users.create(username="alice", password="alice123", full_name="Alice Johnson")
            users.create(username="bob", password="bob123", full_name="Bob Smith")
            users.create(username="carol", password="carol123", full_name="Carol Davis")
        ChatService(session).ensure_general_chat()
