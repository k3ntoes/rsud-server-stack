from datetime import date, datetime

from pydantic import BaseModel, Field


class PhotoSubmit(BaseModel):
    file_name: str
    sort_order: int = 0


class DetailSubmit(BaseModel):
    item_id: int
    score: int = Field(ge=0, le=2)  # 0=risky | 1=minor | 2=standard
    photos: list[PhotoSubmit] = []


class InspectionSubmit(BaseModel):
    room_id: int
    local_timestamp: datetime
    business_date: date
    details: list[DetailSubmit]


class PhotoOut(BaseModel):
    id: int
    photo_file_name: str
    thumbnail_file_name: str | None
    sort_order: int

    model_config = {"from_attributes": True}


class DetailOut(BaseModel):
    id: int
    item_id: int
    item_name_snapshot: str
    score: int
    photos: list[PhotoOut] = []

    model_config = {"from_attributes": True}


class InspectionOut(BaseModel):
    id: int
    room_id: int
    inspector_id: int
    status: str
    business_date: date
    local_timestamp: datetime
    rejection_reason: str | None
    created_at: datetime
    details: list[DetailOut] = []

    model_config = {"from_attributes": True}


class InspectionListItem(BaseModel):
    id: int
    room_id: int
    inspector_id: int
    status: str
    business_date: date
    created_at: datetime
    detail_count: int = 0

    model_config = {"from_attributes": True}


class ApproveRequest(BaseModel):
    pass


class RejectRequest(BaseModel):
    rejection_reason: str
