from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from ..config import (
    ALLOWED_ATTACHMENT_EXTENSIONS,
    ALLOWED_RECORDING_EXTENSIONS,
    MAX_ATTACHMENT_BYTES,
    MAX_RECORDING_BYTES,
    RECORDING_DIR,
    UPLOAD_DIR,
)


class FileValidationError(ValueError):
    pass


class LocalFileStorageStrategy:
    def __init__(self) -> None:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload: UploadFile) -> tuple[str, int]:
        return await _save_upload(
            upload=upload,
            target_dir=UPLOAD_DIR,
            allowed_extensions=ALLOWED_ATTACHMENT_EXTENSIONS,
            max_bytes=MAX_ATTACHMENT_BYTES,
        )


class LocalRecordingStorageStrategy:
    def __init__(self) -> None:
        RECORDING_DIR.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload: UploadFile) -> tuple[str, int]:
        return await _save_upload(
            upload=upload,
            target_dir=RECORDING_DIR,
            allowed_extensions=ALLOWED_RECORDING_EXTENSIONS,
            max_bytes=MAX_RECORDING_BYTES,
        )


async def _save_upload(
    *,
    upload: UploadFile,
    target_dir: Path,
    allowed_extensions: set[str],
    max_bytes: int,
) -> tuple[str, int]:
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(upload.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed_extensions:
        raise FileValidationError("Unsupported file type.")

    content = await upload.read()
    size = len(content)
    if size == 0:
        raise FileValidationError("Empty file is not allowed.")
    if size > max_bytes:
        raise FileValidationError("File is too large.")

    stored_name = f"{uuid4().hex}{suffix}"
    (target_dir / stored_name).write_bytes(content)
    return stored_name, size
