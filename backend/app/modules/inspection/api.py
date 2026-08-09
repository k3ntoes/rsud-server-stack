from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.errors import error_response
from app.core.pagination import paginate
from app.modules.auth.dependencies import get_supervisor_user
from app.modules.auth.models import User
from app.modules.inspection.schemas import (
    InspectionSubmit, InspectionOut, InspectionListItem,
    RejectRequest, PhotoOut,
)
from app.modules.inspection.services import (
    submit_inspection, list_inspections, get_inspection,
    approve_inspection, reject_inspection,
    replace_inspection_photo, InspectionPhotoNotFoundError,
    RoomNotAssignedError, MissingItemsError,
)

router = APIRouter(prefix="/api", tags=["inspection"])


@router.post("/inspections", response_model=InspectionOut, status_code=status.HTTP_201_CREATED)
async def create_inspection(
    body: InspectionSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await submit_inspection(db, current_user.id, body)
    except RoomNotAssignedError as e:
        return error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
            code="ROOM_NOT_ASSIGNED",
        )
    except MissingItemsError as e:
        return error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
            code="SYNC_REQUIRED",
        )
    except ValueError as e:
        return error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
            code="VALIDATION_ERROR",
        )
    except Exception:
        return error_response(
            status.HTTP_409_CONFLICT,
            detail="Duplicate inspection",
            code="DUPLICATE_INSPECTION",
        )


@router.get("/inspections")
async def get_inspections(
    status_filter: str | None = Query(None, alias="status"),
    room_id: int | None = Query(None),
    business_date: str | None = Query(None),
    show_all: bool = Query(False, description="Show all rooms (supervisor only)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Global search across status"),
    sort_by: str | None = Query(None),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import date as date_type
    bd = date_type.fromisoformat(business_date) if business_date else None
    inspections, total = await list_inspections(
        db, status_filter, room_id, bd, page=page, per_page=per_page,
        show_all=show_all, user_id=current_user.id,
        sort_by=sort_by, sort_order=sort_order, search=search,
    )
    items = [
        InspectionListItem(
            id=i.id,
            room_id=i.room_id,
            inspector_id=i.inspector_id,
            status=i.status,
            business_date=i.business_date,
            created_at=i.created_at,
            detail_count=len(i.details),
        )
        for i in inspections
    ]
    return paginate(items, total, page, per_page)


@router.get("/inspections/{inspection_id}", response_model=InspectionOut)
async def get_inspection_by_id(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    inspection = await get_inspection(db, inspection_id)
    if inspection is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    return inspection


@router.post("/inspections/{inspection_id}/approve", response_model=InspectionOut)
async def approve_inspection_endpoint(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_supervisor_user),
):
    inspection = await approve_inspection(db, inspection_id)
    if inspection is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot approve")
    return inspection


@router.post("/inspections/{inspection_id}/reject", response_model=InspectionOut)
async def reject_inspection_endpoint(
    inspection_id: int,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_supervisor_user),
):
    inspection = await reject_inspection(db, inspection_id, body.rejection_reason)
    if inspection is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot reject")
    return inspection


@router.put("/inspections/{inspection_id}/photos/{photo_id}", response_model=PhotoOut)
async def replace_inspection_photo_endpoint(
    inspection_id: int,
    photo_id: int,
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Replace an already-submitted inspection photo (re-upload manual, ADR-0012).

    Access: owner of the inspection OR supervisor/admin. Any status.
    """
    if file is None:
        return error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="File field 'file' is required in multipart/form-data",
            code="MISSING_FILE",
        )
    try:
        photo = await replace_inspection_photo(
            db, current_user, inspection_id, photo_id, file
        )
    except InspectionPhotoNotFoundError:
        return error_response(
            status.HTTP_404_NOT_FOUND,
            detail="Inspection or photo not found",
            code="PHOTO_NOT_FOUND",
        )
    except PermissionError:
        return error_response(
            status.HTTP_403_FORBIDDEN,
            detail="Not allowed to replace this photo",
            code="FORBIDDEN",
        )
    except ValueError as e:
        return error_response(
            status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(e),
            code="FILE_TOO_LARGE",
        )
    return photo
