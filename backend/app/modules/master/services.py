from datetime import datetime, timezone

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sorting import apply_sorting
from app.modules.master.models import Room, InspectionItem, RoomItem


async def list_rooms(
    db: AsyncSession, since: datetime | None = None,
    page: int = 1, per_page: int = 20, search: str | None = None,
    sort_by: str | None = None, sort_order: str = "asc",
) -> tuple[list[Room], int] | list[Room]:
    """
    If `since` is provided, returns unpaginated list (Android sync mode).
    Otherwise returns (paginated_list, total_count).
    """
    if sort_by:
        query = apply_sorting(
            select(Room).where(Room.is_active == True), Room, sort_by, sort_order
        ).order_by(Room.id)
    else:
        query = select(Room).where(Room.is_active == True).order_by(Room.name)

    if since:
        # Baris ber-`updated_at` NULL (data lama sebelum kolom ini diisi) HARUS tetap
        # dikirim — NULL >= since bernilai NULL di SQL sehingga baris tersebut dikecualikan
        # dan sync pertama Android selalu kosong. `is_(None)` menjamin data lama ikut terkirim.
        query = query.where(or_(Room.updated_at.is_(None), Room.updated_at >= since))
        result = await db.execute(query)
        return list(result.scalars().all())

    # Web admin: paginated
    if search:
        pattern = f"%{search}%"
        query = query.where(Room.name.ilike(pattern))

    # Clone query for count (without order_by for performance)
    count_query = select(func.count(Room.id)).where(Room.is_active == True)
    if search:
        pattern = f"%{search}%"
        count_query = count_query.where(Room.name.ilike(pattern))
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    return list(result.scalars().all()), total


async def get_room(db: AsyncSession, room_id: int) -> Room | None:
    return await db.get(Room, room_id)


async def create_room(db: AsyncSession, name: str) -> Room:
    room = Room(name=name, updated_at=datetime.now(timezone.utc))
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


async def update_room(db: AsyncSession, room_id: int, name: str) -> Room | None:
    room = await db.get(Room, room_id)
    if room is None or not room.is_active:
        return None
    room.name = name
    room.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(room)
    return room


async def delete_room(db: AsyncSession, room_id: int) -> bool:
    room = await db.get(Room, room_id)
    if room is None or not room.is_active:
        return False
    room.is_active = False
    room.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return True


# ── Room-Items (pivot) ──


async def list_room_items(db: AsyncSession, since: datetime | None = None) -> list:
    query = select(RoomItem).order_by(RoomItem.room_id, RoomItem.item_id)
    if since:
        # Sync mode: sertakan tombstone (is_active=False) — filter updated_at (bukan
        # created_at) agar penghapusan relasi ikut terkirim ke Android.
        query = query.where(
            or_(RoomItem.updated_at.is_(None), RoomItem.updated_at >= since)
        )
    result = await db.execute(query)
    return list(result.scalars().all())


async def list_items_by_room(db: AsyncSession, room_id: int) -> list:
    result = await db.execute(
        select(RoomItem).where(
            RoomItem.room_id == room_id, RoomItem.is_active == True
        )
    )
    return list(result.scalars().all())


async def list_rooms_by_item(db: AsyncSession, item_id: int) -> list:
    result = await db.execute(
        select(RoomItem).where(
            RoomItem.item_id == item_id, RoomItem.is_active == True
        )
    )
    return list(result.scalars().all())


async def assign_item_to_room(db: AsyncSession, room_id: int, item_id: int):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RoomItem).where(
            RoomItem.room_id == room_id, RoomItem.item_id == item_id
        )
    )
    ri = result.scalar_one_or_none()
    if ri is not None and ri.is_active:
        raise ValueError("Already assigned")  # → 409 di endpoint
    if ri is None:
        ri = RoomItem(room_id=room_id, item_id=item_id)
        db.add(ri)
    else:
        ri.is_active = True  # reaktivasi tombstone (unik constraint tetap terjaga)
    ri.updated_at = now

    # Bump updated_at parent supaya sync /rooms & /inspection-items ikut berubah
    room = await db.get(Room, room_id)
    if room:
        room.updated_at = now
    item = await db.get(InspectionItem, item_id)
    if item:
        item.updated_at = now

    await db.commit()
    await db.refresh(ri)
    return ri


async def unassign_item_from_room(db: AsyncSession, room_id: int, item_id: int) -> bool:
    result = await db.execute(
        select(RoomItem).where(
            RoomItem.room_id == room_id, RoomItem.item_id == item_id
        )
    )
    ri = result.scalar_one_or_none()
    if ri is None or not ri.is_active:
        return False
    now = datetime.now(timezone.utc)
    ri.is_active = False  # soft delete — tombstone terkirim via sync
    ri.updated_at = now

    # Bump updated_at parent supaya sync /rooms & /inspection-items ikut berubah
    room = await db.get(Room, room_id)
    if room:
        room.updated_at = now
    item = await db.get(InspectionItem, item_id)
    if item:
        item.updated_at = now

    await db.commit()
    return True


async def list_items(
    db: AsyncSession, since: datetime | None = None,
    page: int = 1, per_page: int = 20, search: str | None = None,
    sort_by: str | None = None, sort_order: str = "asc",
) -> tuple[list[InspectionItem], int] | list[InspectionItem]:
    """
    If `since` is provided, returns unpaginated list (Android sync mode).
    Otherwise returns (paginated_list, total_count).
    """
    if sort_by:
        query = apply_sorting(
            select(InspectionItem).where(InspectionItem.is_active == True),
            InspectionItem, sort_by, sort_order,
        ).order_by(InspectionItem.id)
    else:
        query = select(InspectionItem).where(InspectionItem.is_active == True).order_by(InspectionItem.name)

    if since:
        # Baris ber-`updated_at` NULL (data lama sebelum kolom ini diisi) HARUS tetap
        # dikirim — NULL >= since bernilai NULL di SQL sehingga baris tersebut dikecualikan
        # dan sync pertama Android selalu kosong. `is_(None)` menjamin data lama ikut terkirim.
        query = query.where(
            or_(InspectionItem.updated_at.is_(None), InspectionItem.updated_at >= since)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    # Web admin: paginated
    if search:
        pattern = f"%{search}%"
        query = query.where(InspectionItem.name.ilike(pattern))

    count_query = select(func.count(InspectionItem.id)).where(InspectionItem.is_active == True)
    if search:
        pattern = f"%{search}%"
        count_query = count_query.where(InspectionItem.name.ilike(pattern))
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    return list(result.scalars().all()), total


async def get_item(db: AsyncSession, item_id: int) -> InspectionItem | None:
    return await db.get(InspectionItem, item_id)


async def create_item(db: AsyncSession, name: str) -> InspectionItem:
    item = InspectionItem(name=name, updated_at=datetime.now(timezone.utc))
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_item(db: AsyncSession, item_id: int, name: str) -> InspectionItem | None:
    item = await db.get(InspectionItem, item_id)
    if item is None or not item.is_active:
        return None
    item.name = name
    item.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item_id: int) -> bool:
    item = await db.get(InspectionItem, item_id)
    if item is None or not item.is_active:
        return False
    item.is_active = False
    item.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return True
