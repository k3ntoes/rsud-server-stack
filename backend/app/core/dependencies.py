from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose.exceptions import ExpiredSignatureError, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.modules.auth.models import User

bearer_scheme = HTTPBearer()


class AuthError(Exception):
    """Raised by auth dependencies to produce a 401 with a machine-readable code.

    Handled centrally in ``main.py`` — FastAPI does not short-circuit when a
    dependency *returns* a Response, so raising a typed exception is the
    reliable way to emit the contract's ``{detail, code}`` shape.
    """

    def __init__(self, detail: str, code: str):
        self.detail = detail
        self.code = code
        super().__init__(detail)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = verify_token(credentials.credentials)
    except ExpiredSignatureError:
        raise AuthError("Token expired", "TOKEN_EXPIRED")
    except JWTError:
        raise AuthError("Invalid token", "TOKEN_INVALID")

    if payload.get("type") != "access":
        raise AuthError("Invalid token type", "TOKEN_INVALID")

    user_id = payload.get("sub")
    if user_id is None:
        raise AuthError("Invalid token", "TOKEN_INVALID")

    try:
        result = await db.execute(
            select(User).where(User.id == int(user_id), User.is_active == True)
        )
    except (ValueError, TypeError):
        raise AuthError("Invalid token", "TOKEN_INVALID")
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthError("User not found", "TOKEN_INVALID")
    return user
