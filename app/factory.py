from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import SECRET_KEY, STATIC_DIR, UPLOAD_DIR
from .database import init_db
from .routes.api import router as api_router
from .routes.pages import router as pages_router
from .routes.ws import router as ws_router
from .services.seed import seed_demo_data


def create_app() -> FastAPI:
    init_db()
    seed_demo_data()

    app = FastAPI(title="Lab7 Corporate Communication App")
    app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

    app.include_router(pages_router)
    app.include_router(api_router)
    app.include_router(ws_router)
    return app
