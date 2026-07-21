import asyncio
from sqlalchemy import select

from app.core.database import async_session
from app.core.security import hash_password
from app.modules.auth.models import User


async def seed_admin():
    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.role == "admin_ppi")
        )
        if result.scalar_one_or_none():
            print("Admin PPI already exists, skipping seed.")
            return

        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin_ppi",
        )
        db.add(admin)
        await db.commit()
        print("Admin PPI seeded: username=admin, password=admin123")


if __name__ == "__main__":
    asyncio.run(seed_admin())
