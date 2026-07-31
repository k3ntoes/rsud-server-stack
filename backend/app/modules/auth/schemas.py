from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    name: str | None = None
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str
    name: str | None = None
    password: str
    role: str


class UserUpdate(BaseModel):
    username: str | None = None
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserListOut(BaseModel):
    id: int
    username: str
    name: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    room_ids: list[int] = []

    model_config = {"from_attributes": True}


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=6)


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class UserRoomOut(BaseModel):
    id: int
    user_id: int
    room_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserRoomAssign(BaseModel):
    user_id: int | None = None
    room_id: int | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserOut
