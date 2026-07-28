from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.inspection.models import Inspection, InspectionDetail, InspectionPhoto
from app.modules.inspection.schemas import InspectionSubmit
from app.modules.auth.models import UserRoom
from app.modules.master.models import InspectionItem, RoomItem


def _base_inspection_query() -> select:
    """Base query with eagerly loaded details and photos."""
    return (
        select(Inspection)
        .options(
            joinedload(Inspection.details).joinedload(InspectionDetail.photos)
        )
    )


async def _refetch_inspection(
    db: AsyncSession, inspection_id: int
) -> Inspection | None:
    result = await db.execute(
        _base_inspection_query().where(Inspection.id == inspection_id)
    )
    return result.unique().scalar_one_or_none()


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
    fetched = await _refetch_inspection(db, inspection.id)
    assert fetched is not None

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
    limit: int = 50,
    offset: int = 0,
    show_all: bool = False,
    user_id: int | None = None,
) -> tuple[list[Inspection], int]:
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
    result = await db.execute(query.offset(offset).limit(limit))
    return list(result.unique().scalars().all()), total


async def get_inspection(db: AsyncSession, inspection_id: int) -> Inspection | None:
    return await _refetch_inspection(db, inspection_id)


async def approve_inspection(db: AsyncSession, inspection_id: int) -> Inspection | None:
    inspection = await db.get(Inspection, inspection_id)
    if inspection is None or inspection.status != "PENDING":
        return None
    inspection.status = "APPROVED"

    # Create job BEFORE commit — atomic with status change (outbox pattern)
    from app.modules.background.services import create_job
    await create_job(db, "recalculate_analytics", inspection_id)

    await db.commit()
    # Re-fetch with relationships for response serialization
    return await _refetch_inspection(db, inspection_id)


async def reject_inspection(
    db: AsyncSession, inspection_id: int, reason: str
) -> Inspection | None:
    inspection = await db.get(Inspection, inspection_id)
    if inspection is None or inspection.status != "PENDING":
        return None
    inspection.status = "REJECTED"
    inspection.rejection_reason = reason
    await db.commit()
    # Re-fetch with relationships for response serialization
    return await _refetch_inspection(db, inspection_id)
