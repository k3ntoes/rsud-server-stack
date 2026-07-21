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


async def save_upload(file: UploadFile) -> str:
    _ensure_upload_dir()
    filename = _safe_filename(file.filename or "photo.jpg")
    path = os.path.join(settings.UPLOAD_DIR, filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return filename


def get_file_path(filename: str) -> str:
    return os.path.join(settings.UPLOAD_DIR, filename)


def file_exists(filename: str) -> bool:
    return os.path.isfile(get_file_path(filename))
