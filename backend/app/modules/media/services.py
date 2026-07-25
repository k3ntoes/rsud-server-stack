import os
import uuid

from fastapi import UploadFile

from app.config import settings


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _ensure_upload_dir():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def _safe_filename(original: str) -> str:
    ext = os.path.splitext(original)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"
    return f"{uuid.uuid4().hex}{ext}"


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB safety net


async def save_upload(file: UploadFile) -> tuple[str, int]:
    _ensure_upload_dir()
    filename = _safe_filename(file.filename or "photo.jpg")
    path = os.path.join(settings.UPLOAD_DIR, filename)

    total_size = 0
    with open(path, "wb") as f:
        while chunk := await file.read(64 * 1024):  # 64KB chunks
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                f.close()
                os.remove(path)
                raise ValueError("File too large. Max 10MB.")
            f.write(chunk)
    return filename, total_size


def get_file_path(filename: str) -> str:
    return os.path.join(settings.UPLOAD_DIR, filename)


def file_exists(filename: str) -> bool:
    return os.path.isfile(get_file_path(filename))
