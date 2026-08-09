from datetime import datetime, timezone

from sqlalchemy import ColumnElement, select, func, or_
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
    now = datetime.now(timezone.utc)
    room.is_active = False
    room.updated_at = now
    await _deactivate_room_items(db, RoomItem.room_id == room_id, now)
    await db.commit()
    return True


# ── Room-Items (pivot) ──


async def _deactivate_room_items(
    db: AsyncSession, condition: ColumnElement[bool], now: datetime
) -> None:
    """Soft-delete RoomItem yang cocok — cegah pivot yatim yang memunculkan
    placeholder "Item #N" di web-admin saat parent dihapus."""
    result = await db.execute(
        select(RoomItem).where(RoomItem.is_active == True, condition)
    )
    for ri in result.scalars().all():
        ri.is_active = False
        ri.updated_at = now


async def list_room_items(db: AsyncSession, since: datetime | None = None) -> list:
    # Urutkan per room memakai sort_order (ADR-0013) — Android membangun checklist
    # dalam urutan ini; tie-breaker item_id agar deterministik.
    query = select(RoomItem).order_by(
        RoomItem.room_id, RoomItem.sort_order, RoomItem.item_id
    )
    if since:
        # Sync mode: sertakan tombstone (is_active=False) — filter updated_at (bukan
        # created_at) agar penghapusan relasi ikut terkirim ke Android.
        query = query.where(
            or_(RoomItem.updated_at.is_(None), RoomItem.updated_at >= since)
        )
    result = await db.execute(query)
    return list(result.scalars().all())


async def list_items_by_room(db: AsyncSession, room_id: int) -> list:
    # Urutan tampilan item per ruangan (ADR-0013): sort_order ASC, item_id ASC
    result = await db.execute(
        select(RoomItem).where(
            RoomItem.room_id == room_id, RoomItem.is_active == True
        ).order_by(RoomItem.sort_order, RoomItem.item_id)
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
        # Append di posisi paling akhir ruangan (ADR-0013) — max(sort_order)+1
        max_result = await db.execute(
            select(func.max(RoomItem.sort_order)).where(RoomItem.room_id == room_id)
        )
        max_order = max_result.scalar()
        ri = RoomItem(
            room_id=room_id, item_id=item_id, sort_order=(max_order + 1 if max_order is not None else 0)
        )
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


async def reorder_room_items(db: AsyncSession, room_id: int, item_ids: list[int]) -> list:
    """Set urutan item ruangan (ADR-0013). `item_ids` harus persis = item aktif milik room.

    Hanya baris yang sort_order-nya berubah yang di-bump `updated_at`-nya,
    supaya sync incremental Android (`GET /api/room-items?since=`) hanya
    mengirim baris yang benar-benar berubah urutannya.
    """
    result = await db.execute(
        select(RoomItem).where(
            RoomItem.room_id == room_id, RoomItem.is_active == True
        )
    )
    rows = list(result.scalars().all())
    active_ids = {r.item_id for r in rows}
    if set(item_ids) != active_ids or len(item_ids) != len(active_ids):
        raise ValueError("item_ids must match active items of room")

    now = datetime.now(timezone.utc)
    order_by_item = {item_id: idx for idx, item_id in enumerate(item_ids)}
    for r in rows:
        new_order = order_by_item[r.item_id]
        if r.sort_order != new_order:
            r.sort_order = new_order
            r.updated_at = now  # bump → sync incremental Android melihat reorder

    await db.commit()
    # Return semua item aktif room dalam urutan baru (UI butuh list penuh),
    # walau hanya baris berubah yang di-bump updated_at-nya.
    return sorted(rows, key=lambda r: (r.sort_order, r.item_id))


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
    now = datetime.now(timezone.utc)
    item.is_active = False
    item.updated_at = now
    await _deactivate_room_items(db, RoomItem.item_id == item_id, now)
    await db.commit()
    return True
