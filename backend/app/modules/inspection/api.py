from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.auth.dependencies import get_supervisor_user
from app.modules.auth.models import User
from app.modules.inspection.schemas import (
    InspectionSubmit, InspectionOut, InspectionListItem,
    RejectRequest,
)
from app.modules.inspection.services import (
    submit_inspection, list_inspections, get_inspection,
    approve_inspection, reject_inspection,
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
    except Exception:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Duplicate inspection or invalid data",
        )


@router.get("/inspections", response_model=list[InspectionListItem])
async def get_inspections(
    status_filter: str | None = Query(None, alias="status"),
    room_id: int | None = Query(None),
    business_date: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_supervisor_user),
):
    from datetime import date as date_type
    bd = date_type.fromisoformat(business_date) if business_date else None
    inspections, _ = await list_inspections(db, status_filter, room_id, bd, limit, offset)
    return [
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


@router.get("/inspections/{inspection_id}", response_model=InspectionOut)
async def get_inspection_by_id(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_supervisor_user),
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
