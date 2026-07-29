from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.master.models import Room, InspectionItem, RoomItem


async def list_rooms(db: AsyncSession, since: datetime | None = None) -> list[Room]:
    query = select(Room).where(Room.is_active == True).order_by(Room.name)
    if since:
        query = query.where(Room.updated_at >= since)
    result = await db.execute(query)
    return list(result.scalars().all())


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
        query = query.where(RoomItem.created_at >= since)
    result = await db.execute(query)
    return list(result.scalars().all())


async def list_items_by_room(db: AsyncSession, room_id: int) -> list:
    result = await db.execute(
        select(RoomItem).where(RoomItem.room_id == room_id)
    )
    return list(result.scalars().all())


async def list_rooms_by_item(db: AsyncSession, item_id: int) -> list:
    result = await db.execute(
        select(RoomItem).where(RoomItem.item_id == item_id)
    )
    return list(result.scalars().all())


async def assign_item_to_room(db: AsyncSession, room_id: int, item_id: int):
    ri = RoomItem(room_id=room_id, item_id=item_id)
    db.add(ri)
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
    if ri is None:
        return False
    await db.delete(ri)
    await db.commit()
    return True


async def list_items(db: AsyncSession, since: datetime | None = None) -> list[InspectionItem]:
    query = select(InspectionItem).where(InspectionItem.is_active == True).order_by(InspectionItem.name)
    if since:
        query = query.where(InspectionItem.updated_at >= since)
    result = await db.execute(query)
    return list(result.scalars().all())


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
