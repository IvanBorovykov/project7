from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..config import TEMPLATES_DIR
from ..database import SessionLocal
from ..models import User
from ..repositories.users import UserRepository


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _session_user_id(request: Request) -> int | None:
    raw_user_id = request.session.get("user_id")
    if raw_user_id is None:
        return None
    try:
        return int(raw_user_id)
    except (TypeError, ValueError):
        request.session.clear()
        return None


def _raise_login_redirect(detail: str) -> None:
    raise HTTPException(status_code=303, detail=detail, headers={"Location": "/login"})


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session) -> User:
    user_id = _session_user_id(request)
    if user_id is None:
        _raise_login_redirect("Not authenticated")
    user = UserRepository(db).get(user_id)
    if user is None:
        request.session.clear()
        _raise_login_redirect("Unknown user")
    return user


def optional_user(request: Request, db: Session) -> User | None:
    user_id = _session_user_id(request)
    if user_id is None:
        return None
    return UserRepository(db).get(user_id)
