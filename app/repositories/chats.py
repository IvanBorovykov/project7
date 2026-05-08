from __future__ import annotations

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from ..models import Attachment, Chat, ChatMember, Message


class ChatRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_user(self, user_id: int) -> list[Chat]:
        query = (
            select(Chat)
            .options(
                selectinload(Chat.members).selectinload(ChatMember.user),
                selectinload(Chat.messages).selectinload(Message.sender),
            )
            .join(ChatMember, ChatMember.chat_id == Chat.id)
            .where(ChatMember.user_id == user_id)
            .order_by(Chat.created_at.desc())
        )
        return list(self.session.scalars(query).unique())

    def get(self, chat_id: int) -> Chat | None:
        query = (
            select(Chat)
            .options(
                selectinload(Chat.members).selectinload(ChatMember.user),
                selectinload(Chat.messages).selectinload(Message.sender),
                selectinload(Chat.messages).selectinload(Message.attachments),
            )
            .where(Chat.id == chat_id)
        )
        return self.session.scalar(query)

    def get_general_chat(self) -> Chat | None:
        return self.session.scalar(select(Chat).where(Chat.chat_type == "general"))

    def create_chat(self, *, name: str | None, chat_type: str) -> Chat:
        chat = Chat(name=name, chat_type=chat_type)
        self.session.add(chat)
        self.session.flush()
        return chat

    def add_member(self, *, chat_id: int, user_id: int) -> ChatMember:
        member = ChatMember(chat_id=chat_id, user_id=user_id)
        self.session.add(member)
        self.session.flush()
        return member

    def get_private_chat(self, first_user_id: int, second_user_id: int) -> Chat | None:
        query = (
            select(Chat)
            .join(ChatMember, ChatMember.chat_id == Chat.id)
            .where(Chat.chat_type == "private", ChatMember.user_id.in_([first_user_id, second_user_id]))
            .group_by(Chat.id)
            .having(func.count(ChatMember.id) == 2)
        )
        chats = list(self.session.scalars(query))
        for chat in chats:
            member_ids = {
                member.user_id
                for member in self.session.scalars(select(ChatMember).where(ChatMember.chat_id == chat.id))
            }
            if member_ids == {first_user_id, second_user_id}:
                return chat
        return None

    def user_in_chat(self, *, chat_id: int, user_id: int) -> bool:
        query = select(ChatMember.id).where(and_(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id))
        return self.session.scalar(query) is not None

    def create_message(self, *, chat_id: int, sender_id: int, content: str) -> Message:
        message = Message(chat_id=chat_id, sender_id=sender_id, content=content)
        self.session.add(message)
        self.session.flush()
        return message

    def add_attachment(
        self,
        *,
        message_id: int,
        original_name: str,
        stored_name: str,
        content_type: str,
        size_bytes: int,
    ) -> Attachment:
        attachment = Attachment(
            message_id=message_id,
            original_name=original_name,
            stored_name=stored_name,
            content_type=content_type,
            size_bytes=size_bytes,
        )
        self.session.add(attachment)
        self.session.flush()
        return attachment
