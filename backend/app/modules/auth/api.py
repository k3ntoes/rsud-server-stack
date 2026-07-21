from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.modules.auth.models import User, UserSession
from app.modules.auth.schemas import LoginRequest, TokenResponse, UserOut
from app.modules.auth.services import authenticate, create_session, refresh_session

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
