import os
from datetime import date

from fastapi import UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.core.sorting import apply_sorting
from app.modules.inspection.models import Inspection, InspectionDetail, InspectionPhoto
from app.modules.inspection.schemas import InspectionSubmit
from app.modules.auth.models import User, UserRoom
from app.modules.master.models import InspectionItem, RoomItem


class InspectionPhotoNotFoundError(Exception):
    """Raised when the inspection or the photo does not exist."""


def _remove_upload_file(filename: str) -> None:
    """Best-effort delete of a stored photo/thumbnail file.

    Swallows OSError — cleanup happens after the DB commit succeeded, so a
    filesystem error here must not turn the request into a failure (nor be
    mistaken for a permission/403 issue upstream).
    """
    try:
        path = os.path.join(settings.UPLOAD_DIR, filename)
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


def _base_inspection_query() -> select:
    """Base query with eagerly loaded details and photos."""
    return (
        select(Inspection)
        .options(
            joinedload(Inspection.details).joinedload(InspectionDetail.photos)
        )
    )


async def _refresh_inspection(
    db: AsyncSession, inspection: Inspection
) -> Inspection:
    await db.refresh(inspection, ["details"])
    for detail in inspection.details:
        await db.refresh(detail, ["photos"])
    return inspection


async def submit_inspection(
    db: AsyncSession,
    inspector_id: int,
    data: InspectionSubmit,
) -> Inspection:
    # Ponytail: composite unique catches duplicates. Let DB do the work.

    # Validate inspector is assigned to this room
    assignment = await db.execute(
        select(UserRoom).where(
            UserRoom.user_id == inspector_id,
            UserRoom.room_id == data.room_id,
        )
    )
    if assignment.scalar_one_or_none() is None:
        raise ValueError(f"Room {data.room_id} is not assigned to you")

    # Validate all items assigned to this room are scored
    room_items = await db.execute(
        select(RoomItem).where(RoomItem.room_id == data.room_id)
    )
    room_item_ids = {ri.item_id for ri in room_items.scalars().all()}
    submitted_ids = {d.item_id for d in data.details}
    missing = room_item_ids - submitted_ids
    if missing:
        raise ValueError(f"Missing items for room: {sorted(missing)}")

    inspection = Inspection(
        room_id=data.room_id,
        inspector_id=inspector_id,
        business_date=data.business_date,
        local_timestamp=data.local_timestamp,
    )
    for d in data.details:
        detail = InspectionDetail(
            item_id=d.item_id,
            item_name_snapshot="",  # filled below
            score=d.score,
        )
        for p in d.photos:
            detail.photos.append(
                InspectionPhoto(photo_file_name=p.file_name, sort_order=p.sort_order)
            )
        inspection.details.append(detail)

    # Snapshot item names from master — one query
    item_ids = {d.item_id for d in data.details}
    result = await db.execute(
        select(InspectionItem).where(
            InspectionItem.id.in_(item_ids), InspectionItem.is_active == True
        )
    )
    items = {item.id: item.name for item in result.scalars().all()}
    for detail in inspection.details:
        detail.item_name_snapshot = items.get(detail.item_id, "Unknown")

    db.add(inspection)
    await db.commit()

    # Re-fetch with relationships loaded — needed for details/photos access
    fetched = await _refresh_inspection(db, inspection)

    # Create thumbnail generation jobs for each uploaded photo
    from app.modules.background.services import create_job
    for detail in fetched.details:
        for photo in detail.photos:
            await create_job(db, "generate_thumbnail", photo.id)
    if any(detail.photos for detail in fetched.details):
        await db.commit()

    return fetched


async def list_inspections(
    db: AsyncSession,
    status: str | None = None,
    room_id: int | None = None,
    business_date: date | None = None,
    page: int = 1,
    per_page: int = 20,
    show_all: bool = False,
    user_id: int | None = None,
    sort_by: str | None = None,
    sort_order: str = "desc",
    search: str | None = None,
) -> tuple[list[Inspection], int]:
    if sort_by:
        query = apply_sorting(select(Inspection), Inspection, sort_by, sort_order).order_by(Inspection.id)
    else:
        query = select(Inspection).order_by(Inspection.created_at.desc())
    count_query = select(func.count(Inspection.id))

    if status:
        query = query.where(Inspection.status == status)
        count_query = count_query.where(Inspection.status == status)
    if room_id:
        query = query.where(Inspection.room_id == room_id)
        count_query = count_query.where(Inspection.room_id == room_id)
    if business_date:
        query = query.where(Inspection.business_date == business_date)
        count_query = count_query.where(Inspection.business_date == business_date)
    if search:
        pattern = f"%{search}%"
        query = query.where(Inspection.status.ilike(pattern))
        count_query = count_query.where(Inspection.status.ilike(pattern))

    # Filter by assigned rooms for supervisor (unless show_all)
    if user_id is not None and not show_all:
        assigned = await db.execute(
            select(UserRoom.room_id).where(UserRoom.user_id == user_id)
        )
        room_ids = [r for r in assigned.scalars().all()]
        if room_ids:
            query = query.where(Inspection.room_id.in_(room_ids))
            count_query = count_query.where(Inspection.room_id.in_(room_ids))

    total = (await db.execute(count_query)).scalar() or 0

    query = query.options(joinedload(Inspection.details))
    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    return list(result.unique().scalars().all()), total


async def get_inspection(db: AsyncSession, inspection_id: int) -> Inspection | None:
    result = await db.execute(
        _base_inspection_query().where(Inspection.id == inspection_id)
    )
    return result.unique().scalar_one_or_none()


async def replace_inspection_photo(
    db: AsyncSession,
    current_user: User,
    inspection_id: int,
    photo_id: int,
    file: UploadFile,
) -> InspectionPhoto:
    """Replace an existing inspection photo's file with a new upload.

    Access: owner of the inspection OR supervisor/admin. Works on any status.
    Order: save new file → update DB → create thumbnail job → commit →
    delete old file + old thumbnail (tolerant of already-missing files).
    """
    inspection = await db.get(Inspection, inspection_id)
    if inspection is None:
        raise InspectionPhotoNotFoundError()

    is_supervisor = current_user.role in ("admin_ppi", "supervisor")
    if inspection.inspector_id != current_user.id and not is_supervisor:
        raise PermissionError("Not allowed to replace this photo")

    # Photo must belong to this inspection
    result = await db.execute(
        select(InspectionPhoto)
        .join(InspectionDetail)
        .where(
            InspectionPhoto.id == photo_id,
            InspectionDetail.inspection_id == inspection_id,
        )
    )
    photo = result.scalar_one_or_none()
    if photo is None:
        raise InspectionPhotoNotFoundError()

    # 1. Save new file (UUID name, 10MB safety net, reused from media module)
    from app.modules.media.services import save_upload
    new_name, _ = await save_upload(file)

    old_name = photo.photo_file_name
    old_thumb = photo.thumbnail_file_name

    # 2. Update DB, 3. queue thumbnail regeneration (outbox, before commit)
    photo.photo_file_name = new_name
    photo.thumbnail_file_name = None
    from app.modules.background.services import create_job
    await create_job(db, "generate_thumbnail", photo.id)
    await db.commit()

    # 4. Delete old files after commit (safe rollback if step 2/3 failed)
    if old_name:
        _remove_upload_file(old_name)
    if old_thumb:
        _remove_upload_file(old_thumb)

    return photo


async def approve_inspection(db: AsyncSession, inspection_id: int) -> Inspection | None:
    inspection = await db.get(Inspection, inspection_id)
    if inspection is None or inspection.status != "PENDING":
        return None
    inspection.status = "APPROVED"

    # Create job BEFORE commit — atomic with status change (outbox pattern)
    from app.modules.background.services import create_job
    await create_job(db, "recalculate_analytics", inspection_id)

    inspection = await _refresh_inspection(db, inspection)
    await db.commit()
    return inspection


async def reject_inspection(
    db: AsyncSession, inspection_id: int, reason: str
) -> Inspection | None:
    inspection = await db.get(Inspection, inspection_id)
    if inspection is None or inspection.status != "PENDING":
        return None
    inspection.status = "REJECTED"
    inspection.rejection_reason = reason
    inspection = await _refresh_inspection(db, inspection)
    await db.commit()
    return inspection
