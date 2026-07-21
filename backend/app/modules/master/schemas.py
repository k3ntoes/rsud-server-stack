from pydantic import BaseModel


class RoomCreate(BaseModel):
    name: str


class RoomUpdate(BaseModel):
    name: str


class RoomOut(BaseModel):
    id: int
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class ItemCreate(BaseModel):
    name: str


class ItemUpdate(BaseModel):
    name: str


class ItemOut(BaseModel):
    id: int
    name: str
    is_active: bool

    model_config = {"from_attributes": True}
