from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..config import TEMPLATES_DIR
from ..database import SessionLocal
from ..models import User
from ..repositories.users import UserRepository


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=303, detail="Not authenticated")
    user = UserRepository(db).get(int(user_id))
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=303, detail="Unknown user")
    return user


def optional_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return UserRepository(db).get(int(user_id))
