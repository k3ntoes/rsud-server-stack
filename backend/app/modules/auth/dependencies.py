from fastapi import Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.modules.auth.models import User


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin_ppi":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def get_supervisor_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("admin_ppi", "supervisor"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Supervisor access required")
    return current_user
