from datetime import datetime

from pydantic import BaseModel


class RoomCreate(BaseModel):
    name: str


class RoomUpdate(BaseModel):
    name: str


class RoomOut(BaseModel):
    id: int
    name: str
    is_active: bool
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ItemCreate(BaseModel):
    name: str


class ItemUpdate(BaseModel):
    name: str


class ItemOut(BaseModel):
    id: int
    name: str
    is_active: bool
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoomItemOut(BaseModel):
    id: int
    room_id: int
    item_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RoomItemAssign(BaseModel):
    item_id: int | None = None
    room_id: int | None = None


class SyncResponse(BaseModel):
    data: list
    synced_at: datetime
