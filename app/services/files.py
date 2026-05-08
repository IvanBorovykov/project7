from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from ..config import ALLOWED_ATTACHMENT_EXTENSIONS, MAX_ATTACHMENT_BYTES, UPLOAD_DIR


class FileValidationError(ValueError):
    pass


class LocalFileStorageStrategy:
    def __init__(self) -> None:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload: UploadFile) -> tuple[str, int]:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in ALLOWED_ATTACHMENT_EXTENSIONS:
            raise FileValidationError("Unsupported file type.")

        content = await upload.read()
        size = len(content)
        if size == 0:
            raise FileValidationError("Empty file is not allowed.")
        if size > MAX_ATTACHMENT_BYTES:
            raise FileValidationError("File is too large.")

        stored_name = f"{uuid4().hex}{suffix}"
        (UPLOAD_DIR / stored_name).write_bytes(content)
        return stored_name, size
