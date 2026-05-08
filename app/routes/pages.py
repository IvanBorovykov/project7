from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..repositories.users import UserRepository
from ..services.auth import AuthService
from ..services.chats import ChatService
from ..services.meetings import MeetingService
from ..services.notifications import NotificationService
from .deps import get_current_user, get_db, optional_user, templates


router = APIRouter()


def _redirect(path: str) -> RedirectResponse:
    return RedirectResponse(url=path, status_code=303)


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    user = optional_user(request, db)
    return _redirect("/dashboard" if user else "/login")


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    user = optional_user(request, db)
    if user:
        return _redirect("/dashboard")
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = AuthService(db).login(username, password)
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password."},
            status_code=400,
        )
    request.session["user_id"] = user.id
    return _redirect("/dashboard")


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return _redirect("/login")


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    meeting_service = MeetingService(db)
    chat_service = ChatService(db)
    notification_service = NotificationService(db)
    users = [candidate for candidate in UserRepository(db).list_all() if candidate.id != user.id]
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "current_user": user,
            "upcoming_meetings": meeting_service.upcoming_for_user(user.id),
            "recent_chats": chat_service.list_for_user(user.id),
            "notifications": notification_service.list_for_user(user.id),
            "users": users,
        },
    )


@router.get("/profile")
def profile(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse("profile.html", {"request": request, "current_user": user})


@router.get("/meetings")
def meetings_list(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    users = [candidate for candidate in UserRepository(db).list_all() if candidate.id != user.id]
    return templates.TemplateResponse(
        "meetings/list.html",
        {
            "request": request,
            "current_user": user,
            "meetings": MeetingService(db).list_for_user(user.id),
            "users": users,
        },
    )


@router.get("/meetings/{meeting_id}")
def meeting_detail(meeting_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    meeting = MeetingService(db).get(meeting_id)
    if meeting is None:
        return _redirect("/meetings")

    livekit_room = MeetingService(db).video_provider.build_room_config(
        room_name=meeting.room_name,
        display_name=user.full_name,
    )
    return templates.TemplateResponse(
        "meetings/detail.html",
        {
            "request": request,
            "current_user": user,
            "meeting": meeting,
            "livekit_room": livekit_room,
        },
    )


@router.get("/chats")
def chats_list(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    users = [candidate for candidate in UserRepository(db).list_all() if candidate.id != user.id]
    return templates.TemplateResponse(
        "chats/list.html",
        {
            "request": request,
            "current_user": user,
            "chats": ChatService(db).list_for_user(user.id),
            "users": users,
        },
    )


@router.get("/chats/{chat_id}")
def chat_detail(chat_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    chat = ChatService(db).get(chat_id)
    if chat is None:
        return _redirect("/chats")
    if not any(member.user_id == user.id for member in chat.members):
        return _redirect("/chats")

    return templates.TemplateResponse(
        "chats/detail.html",
        {
            "request": request,
            "current_user": user,
            "chat": chat,
        },
    )
