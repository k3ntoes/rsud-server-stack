from datetime import datetime, timezone, timedelta
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.modules.auth.models import User, UserSession


async def authenticate(db: AsyncSession, username: str, password: str) -> User | None:
    result = await db.execute(
        select(User).where(User.username == username, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


async def create_user(db: AsyncSession, username: str, password: str, role: str) -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_session(db: AsyncSession, user: User) -> UserSession:
    token = create_refresh_token({"sub": str(user.id), "jti": secrets.token_hex(16)})
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    session = UserSession(
        user_id=user.id, refresh_token=token, expires_at=expires_at
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def refresh_session(
    db: AsyncSession, refresh_token: str
) -> tuple[str, str, User] | None:
    try:
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            return None
    except Exception:
        return None

    result = await db.execute(
        select(UserSession).where(
            UserSession.refresh_token == refresh_token,
            UserSession.is_active == True,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        return None

    # Token rotation: revoke old, issue new
    session.is_active = False
    user = await db.get(User, session.user_id)
    if user is None or not user.is_active:
        await db.commit()
        return None

    new_session = await create_session(db, user)
    new_access = create_access_token({"sub": str(user.id)})
    return new_access, new_session.refresh_token, user


async def revoke_session(db: AsyncSession, session_id: int) -> None:
    session = await db.get(UserSession, session_id)
    if session:
        session.is_active = False
        await db.commit()
