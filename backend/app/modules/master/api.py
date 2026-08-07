from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.pagination import paginate
from app.modules.auth.dependencies import get_admin_user
from app.modules.auth.models import User
from app.modules.master.schemas import (
    RoomCreate, RoomUpdate, RoomOut,
    ItemCreate, ItemUpdate, ItemOut,
    RoomItemOut, RoomItemAssign, RoomItemReorder,
    SyncResponse,
)
from app.modules.master.services import (
    list_rooms, get_room, create_room, update_room, delete_room,
    list_items, get_item, create_item, update_item, delete_item,
    list_room_items, list_items_by_room, list_rooms_by_item,
    assign_item_to_room, unassign_item_from_room, reorder_room_items,
)

router = APIRouter(prefix="/api", tags=["master"])


# ── Rooms ──

@router.get("/rooms")
async def get_rooms(
    since: str | None = Query(None, description="Sync timestamp ISO 8601"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=10000),
    search: str | None = Query(None),
    sort_by: str | None = Query(None),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    dt = datetime.fromisoformat(since) if since else None
    data = await list_rooms(db, since=dt, page=page, per_page=per_page,
                            search=search, sort_by=sort_by, sort_order=sort_order)
    if since:
        return SyncResponse(
            data=[RoomOut.model_validate(r).model_dump() for r in data],
            synced_at=datetime.now(timezone.utc),
        )
    items, total = data
    return paginate([RoomOut.model_validate(r) for r in items], total, page, per_page)


@router.get("/rooms/{room_id}", response_model=RoomOut)
async def get_room_by_id(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    room = await get_room(db, room_id)
    if room is None or not room.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


@router.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
async def create_room_endpoint(
    body: RoomCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    try:
        return await create_room(db, body.name)
    except Exception:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Room name already exists")


@router.put("/rooms/{room_id}", response_model=RoomOut)
async def update_room_endpoint(
    room_id: int,
    body: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    room = await update_room(db, room_id, body.name)
    if room is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room_endpoint(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    if not await delete_room(db, room_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Room not found")


# ── Inspection Items ──

@router.get("/inspection-items")
async def get_items(
    since: str | None = Query(None, description="Sync timestamp ISO 8601"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=10000),
    search: str | None = Query(None),
    sort_by: str | None = Query(None),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    dt = datetime.fromisoformat(since) if since else None
    data = await list_items(db, since=dt, page=page, per_page=per_page,
                            search=search, sort_by=sort_by, sort_order=sort_order)
    if since:
        return SyncResponse(
            data=[ItemOut.model_validate(i).model_dump() for i in data],
            synced_at=datetime.now(timezone.utc),
        )
    items, total = data
    return paginate([ItemOut.model_validate(i) for i in items], total, page, per_page)


@router.get("/inspection-items/{item_id}", response_model=ItemOut)
async def get_item_by_id(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = await get_item(db, item_id)
    if item is None or not item.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.post("/inspection-items", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item_endpoint(
    body: ItemCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    try:
        return await create_item(db, body.name)
    except Exception:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Item name already exists")


@router.put("/inspection-items/{item_id}", response_model=ItemOut)
async def update_item_endpoint(
    item_id: int,
    body: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    item = await update_item(db, item_id, body.name)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.delete("/inspection-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item_endpoint(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    if not await delete_item(db, item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")


# ── Room-Items (pivot) ──


@router.get("/room-items")
async def get_room_items(
    since: str | None = Query(None, description="Sync timestamp ISO 8601"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    dt = datetime.fromisoformat(since) if since else None
    data = await list_room_items(db, dt)
    return SyncResponse(
        data=[RoomItemOut.model_validate(r).model_dump() for r in data],
        synced_at=datetime.now(timezone.utc),
    )


# Room → Items


@router.get("/rooms/{room_id}/items")
async def get_room_items_by_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    room = await get_room(db, room_id)
    if room is None or not room.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Room not found")
    data = await list_items_by_room(db, room_id)
    return [RoomItemOut.model_validate(r) for r in data]


@router.post("/rooms/{room_id}/items", status_code=status.HTTP_201_CREATED)
async def assign_item_to_room_endpoint(
    room_id: int,
    body: RoomItemAssign,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    if body.item_id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="item_id required")
    try:
        ri = await assign_item_to_room(db, room_id, body.item_id)
        return RoomItemOut.model_validate(ri)
    except Exception:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Already assigned or invalid room/item")


@router.delete("/rooms/{room_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_item_from_room_endpoint(
    room_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    if not await unassign_item_from_room(db, room_id, item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assignment not found")


@router.put("/rooms/{room_id}/items/reorder")
async def reorder_room_items_endpoint(
    room_id: int,
    body: RoomItemReorder,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    """Atur urutan item ruangan (ADR-0013) — body `{ "item_ids": [...] }` terurut."""
    room = await get_room(db, room_id)
    if room is None or not room.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Room not found")
    try:
        rows = await reorder_room_items(db, room_id, body.item_ids)
    except ValueError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="item_ids must match active items of room",
        )
    return [RoomItemOut.model_validate(r) for r in rows]


# Item → Rooms


@router.get("/inspection-items/{item_id}/rooms")
async def get_rooms_by_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = await get_item(db, item_id)
    if item is None or not item.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")
    data = await list_rooms_by_item(db, item_id)
    return [RoomItemOut.model_validate(r) for r in data]


@router.post("/inspection-items/{item_id}/rooms", status_code=status.HTTP_201_CREATED)
async def assign_room_to_item_endpoint(
    item_id: int,
    body: RoomItemAssign,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    if body.room_id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="room_id required")
    try:
        ri = await assign_item_to_room(db, body.room_id, item_id)
        return RoomItemOut.model_validate(ri)
    except Exception:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Already assigned or invalid room/item")


@router.delete("/inspection-items/{item_id}/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_room_from_item_endpoint(
    item_id: int,
    room_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    if not await unassign_item_from_room(db, room_id, item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assignment not found")
