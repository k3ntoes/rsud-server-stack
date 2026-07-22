from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.inspection.models import Inspection, InspectionDetail, InspectionPhoto
from app.modules.inspection.schemas import InspectionSubmit


async def submit_inspection(
    db: AsyncSession,
    inspector_id: int,
    data: InspectionSubmit,
) -> Inspection:
    # Ponytail: composite unique catches duplicates. Let DB do the work.
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
    from app.modules.master.models import InspectionItem

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
    # Re-fetch with relationships loaded for response serialization
    result = await db.execute(
        select(Inspection)
        .where(Inspection.id == inspection.id)
        .options(
            joinedload(Inspection.details).joinedload(InspectionDetail.photos)
        )
    )
    return result.unique().scalar_one()


async def list_inspections(
    db: AsyncSession,
    status: str | None = None,
    room_id: int | None = None,
    business_date: date | None = None,
    limit: int = 50,
    offset: int = 0,
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

    total = (await db.execute(count_query)).scalar() or 0

    query = query.options(joinedload(Inspection.details))
    result = await db.execute(query.offset(offset).limit(limit))
    return list(result.unique().scalars().all()), total


async def get_inspection(db: AsyncSession, inspection_id: int) -> Inspection | None:
    result = await db.execute(
        select(Inspection)
        .where(Inspection.id == inspection_id)
        .options(
            joinedload(Inspection.details).joinedload(InspectionDetail.photos)
        )
    )
    return result.unique().scalar_one_or_none()


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
    result = await db.execute(
        select(Inspection)
        .where(Inspection.id == inspection_id)
        .options(
            joinedload(Inspection.details).joinedload(InspectionDetail.photos)
        )
    )
    return result.unique().scalar_one_or_none()


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
    result = await db.execute(
        select(Inspection)
        .where(Inspection.id == inspection_id)
        .options(
            joinedload(Inspection.details).joinedload(InspectionDetail.photos)
        )
    )
    return result.unique().scalar_one_or_none()
