import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse

from app.core.dependencies import get_current_user
from app.core.errors import error_response
from app.config import settings
from app.modules.auth.models import User
from app.modules.media.services import save_upload

router = APIRouter(prefix="/api", tags=["media"])


@router.post("/upload")
async def upload_file(
    file: UploadFile | None = File(None),
    _: User = Depends(get_current_user),
):
    if file is None:
        return error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="File field 'file' is required in multipart/form-data",
            code="MISSING_FILE",
        )
    try:
        filename, file_size = await save_upload(file)
    except ValueError as e:
        return error_response(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
            code="FILE_TOO_LARGE",
        )
    return {
        "photo_file_name": filename,
        "thumbnail_file_name": None,
        "file_size": file_size,
    }


@router.get("/media/{filename}")
async def serve_file(
    filename: str,
    _: User = Depends(get_current_user),
):
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(filepath)
