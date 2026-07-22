from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import FileResponse
from jose import jwt, JWTError

from app.config import settings
from app.core.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.media.services import save_upload, get_file_path, file_exists

router = APIRouter(prefix="/api", tags=["media"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
):
    filename = await save_upload(file)
    return {"file_name": filename}


@router.get("/media/{filename}")
async def serve_file(
    filename: str,
    _: User = Depends(get_current_user),
):
    if not file_exists(filename):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(get_file_path(filename))


@router.post("/media/token")
async def generate_token(
    filename: str = Query(...),
    _: User = Depends(get_current_user),
):
    """Generate a one-time access token for a media file."""
    if not file_exists(filename):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = jwt.encode(
        {"fn": filename, "exp": expire, "type": "media_access"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return {"token": token, "expires_in": 300}


@router.get("/media/access/{token}")
async def access_file(token: str):
    """Access a media file via one-time token (no auth header needed)."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "media_access":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        filename = payload.get("fn")
        if not filename:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if not file_exists(filename):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(get_file_path(filename))
