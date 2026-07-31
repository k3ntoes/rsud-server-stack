from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.errors import error_response
from app.core.pagination import paginate
from app.core.security import create_access_token
from app.modules.auth.dependencies import get_admin_user
from app.modules.auth.models import User, UserSession, UserRoom
from app.modules.master.models import Room
from app.modules.master.schemas import SyncResponse, RoomOut
from app.modules.auth.schemas import (
    LoginRequest, TokenResponse, UserOut,
    UserCreate, UserUpdate, UserListOut, ChangePasswordRequest,
    AdminResetPasswordRequest, RefreshRequest,
    UserRoomOut, UserRoomAssign,
)
from app.modules.auth.services import (
    authenticate, create_session, refresh_session, create_user,
    list_users, update_user, deactivate_user, change_password,
    admin_reset_password,
    list_all_user_rooms, list_rooms_by_user, list_users_by_room,
    assign_user_to_room, unassign_user_from_room, get_user_room_ids,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    session = await create_session(db, user)
    access_token = create_access_token({"sub": str(user.id)})

    response.set_cookie(
        key="refresh_token",
        value=session.refresh_token,
        httponly=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=session.refresh_token,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest | None = None,
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db),
):
    # Android sends refresh_token in body; Web sends via httpOnly cookie
    refresh_token = None
    if body and body.refresh_token:
        refresh_token = body.refresh_token
    if not refresh_token:
        refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return error_response(
            status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            code="TOKEN_EXPIRED",
        )

    result = await refresh_session(db, refresh_token)
    if result is None:
        return error_response(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            code="TOKEN_INVALID",
        )

    new_access, new_refresh, user = result
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        user=UserOut.model_validate(user),
    )


@router.post("/logout")
async def logout(
    body: RefreshRequest | None = None,
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db),
):
    # Android sends refresh_token in body; Web sends via httpOnly cookie
    refresh_token = None
    if body and body.refresh_token:
        refresh_token = body.refresh_token
    if not refresh_token:
        refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        result = await db.execute(
            select(UserSession).where(UserSession.refresh_token == refresh_token)
        )
        session = result.scalar_one_or_none()
        if session:
            session.is_active = False
            await db.commit()
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


# ── User Management (admin only) ──


@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    sort_by: str | None = Query(None),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    users, total = await list_users(db, page, per_page, search, sort_by, sort_order)
    items = []
    for u in users:
        room_ids = await get_user_room_ids(db, u.id)
        items.append(UserListOut(
            id=u.id,
            username=u.username,
            name=u.name,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
            room_ids=room_ids,
        ))
    return paginate(items, total, page, per_page)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    # ponytail: broad except — catches DB errors too, not just dupes.
    # Narrow to IntegrityError if false-positives become an issue.
    try:
        user = await create_user(db, body.username, body.password, body.role, body.name)
        return UserOut.model_validate(user)
    except Exception:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already exists")


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user_endpoint(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    user = await update_user(db, user_id, body.username, body.name, body.role, body.is_active)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    if not await deactivate_user(db, user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")


# ── Admin Reset Password (admin only) ──


@router.put("/users/{user_id}/reset-password")
async def admin_reset_password_endpoint(
    user_id: int,
    body: AdminResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    user = await admin_reset_password(db, user_id, body.new_password)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "Password reset successfully"}


# ── User-Room (pivot) ──


@router.get("/user-rooms")
async def get_user_rooms_bulk(
    since: str | None = Query(None, description="Sync timestamp ISO 8601"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Bulk sync all user-room associations (Android)."""
    dt = datetime.fromisoformat(since) if since else None
    data = await list_all_user_rooms(db, dt)
    return SyncResponse(
        data=[UserRoomOut.model_validate(r).model_dump() for r in data],
        synced_at=datetime.now(timezone.utc),
    )


@router.get("/me/rooms")
async def get_my_rooms(
    since: str | None = Query(None, description="Sync timestamp ISO 8601"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List room assignments for current user (Android sync)."""
    result = await db.execute(
        select(UserRoom).where(UserRoom.user_id == current_user.id)
    )
    ur_rows = result.scalars().all()
    room_ids = [ur.room_id for ur in ur_rows]

    if since and room_ids:
        dt = datetime.fromisoformat(since)
        rooms_result = await db.execute(
            select(Room).where(
                Room.id.in_(room_ids), Room.updated_at >= dt
            )
        )
    elif room_ids:
        rooms_result = await db.execute(
            select(Room).where(Room.id.in_(room_ids))
        )
    else:
        data = []
        return SyncResponse(data=data, synced_at=datetime.now(timezone.utc))

    data = rooms_result.scalars().all()
    return SyncResponse(
        data=[RoomOut.model_validate(r).model_dump() for r in data],
        synced_at=datetime.now(timezone.utc),
    )


# Admin: Room → Users


@router.get("/rooms/{room_id}/users")
async def get_room_users(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    data = await list_users_by_room(db, room_id)
    return [UserRoomOut.model_validate(r) for r in data]


@router.post("/rooms/{room_id}/users", status_code=status.HTTP_201_CREATED)
async def assign_user_to_room_endpoint(
    room_id: int,
    body: UserRoomAssign,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    if body.user_id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="user_id required")
    try:
        ur = await assign_user_to_room(db, body.user_id, room_id)
        return UserRoomOut.model_validate(ur)
    except Exception:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Already assigned or invalid user/room")


@router.delete("/rooms/{room_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_user_from_room_endpoint(
    room_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    if not await unassign_user_from_room(db, user_id, room_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assignment not found")


# Admin: User → Rooms


@router.get("/users/{user_id}/rooms")
async def get_user_rooms(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    data = await list_rooms_by_user(db, user_id)
    return [UserRoomOut.model_validate(r) for r in data]


@router.post("/users/{user_id}/rooms", status_code=status.HTTP_201_CREATED)
async def assign_room_to_user_endpoint(
    user_id: int,
    body: UserRoomAssign,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    if body.room_id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="room_id required")
    try:
        ur = await assign_user_to_room(db, user_id, body.room_id)
        return UserRoomOut.model_validate(ur)
    except Exception:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Already assigned or invalid user/room")


@router.delete("/users/{user_id}/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_room_from_user_endpoint(
    user_id: int,
    room_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    if not await unassign_user_from_room(db, user_id, room_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assignment not found")


# ── Change Password (any authenticated user) ──


@router.post("/change-password")
async def change_password_endpoint(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await change_password(db, current_user, body.old_password, body.new_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    return {"message": "Password changed successfully"}
