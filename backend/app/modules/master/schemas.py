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


class SyncResponse(BaseModel):
    data: list
    synced_at: datetime
