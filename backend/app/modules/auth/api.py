from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.modules.auth.dependencies import get_admin_user
from app.modules.auth.models import User, UserSession
from app.modules.auth.schemas import (
    LoginRequest, TokenResponse, UserOut,
    UserCreate, UserUpdate, UserListOut, ChangePasswordRequest,
    AdminResetPasswordRequest,
)
from app.modules.auth.services import (
    authenticate, create_session, refresh_session, create_user,
    list_users, update_user, deactivate_user, change_password,
    admin_reset_password,
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
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

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
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    result = await refresh_session(db, refresh_token)
    if result is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

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
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
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


@router.get("/users", response_model=list[UserListOut])
async def get_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    return await list_users(db)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    # ponytail: broad except — catches DB errors too, not just dupes.
    # Narrow to IntegrityError if false-positives become an issue.
    try:
        user = await create_user(db, body.username, body.password, body.role)
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
    user = await update_user(db, user_id, body.username, body.role, body.is_active)
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
