from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_admin_user
from app.modules.auth.models import User
from app.modules.master.schemas import (
    RoomCreate, RoomUpdate, RoomOut,
    ItemCreate, ItemUpdate, ItemOut,
)
from app.modules.master.services import (
    list_rooms, get_room, create_room, update_room, delete_room,
    list_items, get_item, create_item, update_item, delete_item,
)

router = APIRouter(prefix="/api", tags=["master"])


# ── Rooms ──

@router.get("/rooms", response_model=list[RoomOut])
async def get_rooms(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    return await list_rooms(db)


@router.get("/rooms/{room_id}", response_model=RoomOut)
async def get_room_by_id(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
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

@router.get("/inspection-items", response_model=list[ItemOut])
async def get_items(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    return await list_items(db)


@router.get("/inspection-items/{item_id}", response_model=ItemOut)
async def get_item_by_id(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
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
