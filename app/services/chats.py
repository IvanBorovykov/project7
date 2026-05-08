from __future__ import annotations

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..models import Chat, Message
from ..repositories.chats import ChatRepository
from ..repositories.users import UserRepository
from .files import LocalFileStorageStrategy
from .notifications import NotificationService


class ChatService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.chats = ChatRepository(session)
        self.users = UserRepository(session)
        self.notifications = NotificationService(session)
        self.storage = LocalFileStorageStrategy()

    def list_for_user(self, user_id: int) -> list[Chat]:
        return self.chats.list_for_user(user_id)

    def get(self, chat_id: int) -> Chat | None:
        return self.chats.get(chat_id)

    def ensure_general_chat(self) -> Chat:
        chat = self.chats.get_general_chat()
        if chat is None:
            chat = self.chats.create_chat(name="General Company Chat", chat_type="general")
            for user in self.users.list_all():
                self.chats.add_member(chat_id=chat.id, user_id=user.id)
        return chat

    def create_or_get_private_chat(self, *, current_user_id: int, other_user_id: int) -> Chat:
        existing = self.chats.get_private_chat(current_user_id, other_user_id)
        if existing is not None:
            return existing

        first = self.users.get(current_user_id)
        second = self.users.get(other_user_id)
        if first is None or second is None:
            raise ValueError("User not found.")

        chat = self.chats.create_chat(name=f"{first.full_name} / {second.full_name}", chat_type="private")
        self.chats.add_member(chat_id=chat.id, user_id=current_user_id)
        self.chats.add_member(chat_id=chat.id, user_id=other_user_id)
        self.notifications.create(
            user_id=other_user_id,
            kind="private_chat",
            content=f"{first.full_name} opened a private chat with you.",
        )
        return chat

    async def send_message(
        self,
        *,
        chat_id: int,
        sender_id: int,
        content: str,
        upload: UploadFile | None = None,
    ) -> Message:
        if not self.chats.user_in_chat(chat_id=chat_id, user_id=sender_id):
            raise ValueError("User is not a member of this chat.")
        if not content.strip() and upload is None:
            raise ValueError("Message content or file is required.")

        message = self.chats.create_message(chat_id=chat_id, sender_id=sender_id, content=content.strip())
        if upload is not None and upload.filename:
            stored_name, size = await self.storage.save_upload(upload)
            self.chats.add_attachment(
                message_id=message.id,
                original_name=upload.filename,
                stored_name=stored_name,
                content_type=upload.content_type or "application/octet-stream",
                size_bytes=size,
            )

        chat = self.chats.get(chat_id)
        if chat is None:
            raise ValueError("Chat not found.")

        sender = self.users.get(sender_id)
        if sender is None:
            raise ValueError("Sender not found.")

        if chat.chat_type == "private":
            for member in chat.members:
                if member.user_id != sender_id:
                    self.notifications.create(
                        user_id=member.user_id,
                        kind="private_message",
                        content=f"New private message from {sender.full_name}.",
                    )

        self.session.flush()
        return self.chats.get(chat_id).messages[-1]
