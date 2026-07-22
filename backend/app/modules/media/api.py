from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse

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
