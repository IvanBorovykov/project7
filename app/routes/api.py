from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..services.chats import ChatService
from ..services.files import FileValidationError
from ..services.livekit import LiveKitConfigurationError
from ..services.meetings import MeetingService
from ..services.notifications import NotificationService
from ..ws.manager import manager
from .deps import get_current_user, get_db


router = APIRouter(prefix="/api")


def _redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=303)


@router.post("/meetings")
def create_meeting(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    starts_at: str = Form(...),
    duration_minutes: int = Form(...),
    participant_ids: list[int] = Form(default=[]),
    recording_enabled: bool = Form(default=False),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    try:
        MeetingService(db).create_meeting(
            organizer_id=user.id,
            title=title,
            description=description,
            starts_at_raw=starts_at,
            duration_minutes=duration_minutes,
            participant_ids=participant_ids,
            recording_enabled=recording_enabled,
        )
    except ValueError as exc:
        return _redirect(f"/meetings?error={quote(str(exc))}")
    db.commit()
    return _redirect("/meetings")


@router.post("/meetings/{meeting_id}/status")
async def update_meeting_status(
    meeting_id: int,
    request: Request,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    participant = MeetingService(db).update_participation(meeting_id=meeting_id, user_id=user.id, status=status)
    notifications = NotificationService(db).list_for_user(participant.meeting.organizer_id, limit=1)
    db.commit()
    if notifications:
        await manager.notify_user(
            participant.meeting.organizer_id,
            {"kind": notifications[0].kind, "content": notifications[0].content},
        )
    return _redirect(f"/meetings/{meeting_id}")


@router.post("/meetings/{meeting_id}/recording")
def save_recording(
    meeting_id: int,
    request: Request,
    status: str = Form(...),
    external_url: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    meeting = MeetingService(db).get(meeting_id)
    if meeting is None or meeting.organizer_id != user.id:
        return _redirect("/meetings")
    MeetingService(db).save_recording(
        meeting_id=meeting_id,
        status=status,
        external_url=external_url.strip() or None,
    )
    db.commit()
    return _redirect(f"/meetings/{meeting_id}")


@router.post("/chats/private")
def create_private_chat(
    request: Request,
    other_user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    try:
        chat = ChatService(db).create_or_get_private_chat(current_user_id=user.id, other_user_id=other_user_id)
    except ValueError as exc:
        return _redirect(f"/chats?error={quote(str(exc))}")
    db.commit()
    return _redirect(f"/chats/{chat.id}")


@router.post("/chats/{chat_id}/messages")
async def create_message(
    chat_id: int,
    request: Request,
    content: str = Form(""),
    attachment: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    service = ChatService(db)
    try:
        await service.send_message(chat_id=chat_id, sender_id=user.id, content=content, upload=attachment)
    except FileValidationError as exc:
        return RedirectResponse(f"/chats/{chat_id}?error={quote(str(exc))}", status_code=303)
    except ValueError as exc:
        destination = f"/chats/{chat_id}" if service.get(chat_id) is not None else "/chats"
        return RedirectResponse(f"{destination}?error={quote(str(exc))}", status_code=303)
    db.commit()
    refreshed = ChatService(db).get(chat_id)
    if refreshed is None or not refreshed.messages:
        return _redirect("/chats")
    last_message = refreshed.messages[-1]
    attachment_url = ""
    attachment_name = ""
    if last_message.attachments:
        attachment = last_message.attachments[0]
        attachment_url = f"/uploads/{attachment.stored_name}"
        attachment_name = attachment.original_name

    await manager.broadcast_chat(
        chat_id,
        {
            "sender_id": str(last_message.sender_id),
            "sender": last_message.sender.full_name,
            "content": last_message.content,
            "created_at": last_message.created_at.strftime("%Y-%m-%d %H:%M"),
            "attachment_url": attachment_url,
            "attachment_name": attachment_name,
        },
    )

    for member in refreshed.members:
        if member.user_id != user.id and refreshed.chat_type == "private":
            latest = NotificationService(db).list_for_user(member.user_id, limit=1)
            if latest:
                await manager.notify_user(member.user_id, {"kind": latest[0].kind, "content": latest[0].content})
    return _redirect(f"/chats/{chat_id}")


@router.post("/livekit/token")
def create_livekit_token(
    request: Request,
    room_name: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    meeting_service = MeetingService(db)
    try:
        participant_token = meeting_service.video_provider.generate_participant_token(
            room_name=room_name,
            participant_identity=user.username,
            participant_name=user.full_name,
        )
    except LiveKitConfigurationError as exc:
        return JSONResponse({"error": str(exc)}, status_code=503)

    room_config = meeting_service.video_provider.build_room_config(
        room_name=room_name,
        display_name=user.full_name,
    )
    return JSONResponse(
        {
            "server_url": room_config.server_url,
            "participant_token": participant_token,
        },
        status_code=201,
    )
