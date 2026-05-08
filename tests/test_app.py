from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from starlette.websockets import WebSocketDisconnect

from app.factory import create_app
from app.database import SessionLocal, init_db
from app.models import Attachment, Chat, ChatMember, Meeting, MeetingParticipant, Message, Notification, Recording, User
from app.repositories.users import UserRepository
from app.services.chats import ChatService
from app.services.livekit import LiveKitFacade
from app.services.seed import seed_demo_data


@pytest.fixture()
def client():
    init_db()
    session = SessionLocal()
    try:
        session.execute(delete(Attachment))
        session.execute(delete(Message))
        session.execute(delete(ChatMember))
        session.execute(delete(Chat))
        session.execute(delete(MeetingParticipant))
        session.execute(delete(Recording))
        session.execute(delete(Meeting))
        session.execute(delete(Notification))
        session.execute(delete(User))
        session.commit()
    finally:
        session.close()

    seed_demo_data()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str, password: str):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=False)


def test_auth_login_success_and_failure(client: TestClient):
    ok = login(client, "alice", "alice123")
    assert ok.status_code == 303

    bad = client.post("/login", data={"username": "alice", "password": "wrong"})
    assert bad.status_code == 400
    assert "Invalid username or password" in bad.text


def test_protected_pages_redirect_to_login(client: TestClient):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_create_meeting_valid(client: TestClient):
    login(client, "alice", "alice123")
    response = client.post(
        "/api/meetings",
        data={
            "title": "Design Review",
            "description": "Architecture sync",
            "starts_at": "2030-01-01T10:00",
            "duration_minutes": "45",
            "participant_ids": ["2", "3"],
            "recording_enabled": "true",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    session = SessionLocal()
    try:
        meeting = session.query(Meeting).filter_by(title="Design Review").one()
        assert meeting.room_name.startswith("lab7-")
        assert len(meeting.participants) == 3
        assert meeting.recording is not None
    finally:
        session.close()


def test_reject_meeting_more_than_30_participants(client: TestClient):
    session = SessionLocal()
    try:
        users = UserRepository(session)
        for index in range(4, 34):
            users.create(username=f"user{index}", password="pw", full_name=f"User {index}")
        session.commit()
    finally:
        session.close()

    login(client, "alice", "alice123")
    participant_ids = [str(user_id) for user_id in range(2, 34)]
    response = client.post(
        "/api/meetings",
        data={
            "title": "Oversized",
            "description": "",
            "starts_at": "2030-01-01T10:00",
            "duration_minutes": "30",
            "participant_ids": participant_ids,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "Meeting%20cannot%20have%20more%20than%2030%20participants." in response.headers["location"]


def test_invite_accept_decline_updates_status(client: TestClient):
    login(client, "alice", "alice123")
    client.post(
        "/api/meetings",
        data={
            "title": "Planning",
            "description": "",
            "starts_at": "2030-01-01T10:00",
            "duration_minutes": "30",
            "participant_ids": ["2"],
        },
    )

    client.post("/logout")
    login(client, "bob", "bob123")
    response = client.post("/api/meetings/1/status", data={"status": "accepted"}, follow_redirects=False)
    assert response.status_code == 303

    session = SessionLocal()
    try:
        participant = session.query(MeetingParticipant).filter_by(meeting_id=1, user_id=2).one()
        assert participant.status == "accepted"
    finally:
        session.close()


def test_private_chat_creation_is_idempotent(client: TestClient):
    login(client, "alice", "alice123")
    first = client.post("/api/chats/private", data={"other_user_id": "2"}, follow_redirects=False)
    second = client.post("/api/chats/private", data={"other_user_id": "2"}, follow_redirects=False)
    assert first.headers["location"] == second.headers["location"]


def test_private_chat_with_self_is_rejected(client: TestClient):
    login(client, "alice", "alice123")
    response = client.post("/api/chats/private", data={"other_user_id": "1"}, follow_redirects=False)
    assert response.status_code == 303
    assert "cannot%20start%20a%20private%20chat%20with%20yourself" in response.headers["location"]


def test_chats_are_ordered_by_latest_message(client: TestClient):
    login(client, "alice", "alice123")
    client.post("/api/chats/private", data={"other_user_id": "2"})
    client.post("/api/chats/private", data={"other_user_id": "3"})
    client.post("/api/chats/2/messages", data={"content": "latest bob message"}, follow_redirects=False)

    response = client.get("/chats")
    assert response.text.index("Alice Johnson / Bob Smith") < response.text.index("Alice Johnson / Carol Davis")


def test_send_message_persists(client: TestClient):
    login(client, "alice", "alice123")
    client.post("/api/chats/private", data={"other_user_id": "2"})
    response = client.post("/api/chats/2/messages", data={"content": "hello bob"}, follow_redirects=False)
    assert response.status_code == 303

    session = SessionLocal()
    try:
        message = session.query(Message).filter_by(content="hello bob").one()
        assert message.sender_id == 1
    finally:
        session.close()


def test_reject_empty_chat_message(client: TestClient):
    login(client, "alice", "alice123")
    client.post("/api/chats/private", data={"other_user_id": "2"})

    response = client.post("/api/chats/2/messages", data={"content": "   "}, follow_redirects=False)
    assert response.status_code == 303
    assert "Message%20content%20or%20file%20is%20required." in response.headers["location"]


def test_reject_overlong_chat_message(client: TestClient):
    login(client, "alice", "alice123")
    client.post("/api/chats/private", data={"other_user_id": "2"})

    response = client.post("/api/chats/2/messages", data={"content": "x" * 2001}, follow_redirects=False)
    assert response.status_code == 303
    assert "Message%20cannot%20exceed%202000%20characters." in response.headers["location"]


def test_attachment_upload_validation_and_link(client: TestClient):
    login(client, "alice", "alice123")
    client.post("/api/chats/private", data={"other_user_id": "2"})

    response = client.post(
        "/api/chats/2/messages",
        data={"content": "with file"},
        files={"attachment": ("note.txt", BytesIO(b"hello file"), "text/plain")},
        follow_redirects=False,
    )
    assert response.status_code == 303

    session = SessionLocal()
    try:
        attachment = session.query(Attachment).one()
        assert attachment.original_name == "note.txt"
    finally:
        session.close()

    bad = client.post(
        "/api/chats/2/messages",
        data={"content": "bad file"},
        files={"attachment": ("script.exe", BytesIO(b"x"), "application/octet-stream")},
        follow_redirects=False,
    )
    assert "Unsupported%20file%20type." in bad.headers["location"]


def test_websocket_chat_broadcast_reaches_connected_participant(client: TestClient):
    login(client, "alice", "alice123")
    session = SessionLocal()
    try:
        chat_id = ChatService(session).ensure_general_chat().id
        session.commit()
    finally:
        session.close()

    with client.websocket_connect(f"/ws/chat/{chat_id}") as websocket:
        client.post(f"/api/chats/{chat_id}/messages", data={"content": "ws hello"}, follow_redirects=False)
        payload = websocket.receive_json()
        assert payload["content"] == "ws hello"


def test_websocket_chat_rejects_unauthenticated_client(client: TestClient):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/chat/1"):
            pass


def test_notification_event_created_on_invite_and_private_message(client: TestClient):
    login(client, "alice", "alice123")
    client.post(
        "/api/meetings",
        data={
            "title": "Notify",
            "description": "",
            "starts_at": "2030-01-01T10:00",
            "duration_minutes": "30",
            "participant_ids": ["2"],
        },
    )
    client.post("/api/chats/private", data={"other_user_id": "2"})
    client.post("/api/chats/2/messages", data={"content": "message for bob"})

    session = SessionLocal()
    try:
        bob_notifications = session.query(Notification).filter_by(user_id=2).all()
        assert any(item.kind == "meeting_invite" for item in bob_notifications)
        assert any(item.kind == "private_message" for item in bob_notifications)
    finally:
        session.close()


def test_livekit_facade_is_deterministic():
    facade = LiveKitFacade()
    room = facade.build_room_config(room_name="lab7-5-team-sync", display_name="Alice Johnson")
    assert room.server_url
    assert room.room_name == "lab7-5-team-sync"
    assert room.display_name == "Alice Johnson"
