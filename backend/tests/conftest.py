from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.main import app
from app.modules.auth.models import User
from app.modules.master.models import Room, InspectionItem

TEST_DB_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture
async def db_session():
    """Create tables, yield a session, then drop tables."""
    engine = create_async_engine(TEST_DB_URL, echo=False, connect_args={"check_same_thread": False})

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_fk(dbapi_con, _):
        cursor = dbapi_con.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI test client with overridden DB dependency."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Auth helpers ──


async def create_user(session: AsyncSession, username: str, password: str, role: str) -> User:
    user = User(username=username, password_hash=hash_password(password), role=role)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


def auth_header(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


# ── Seed helpers ──


async def seed_room(session: AsyncSession, name: str) -> Room:
    room = Room(name=name)
    session.add(room)
    await session.commit()
    await session.refresh(room)
    return room


async def seed_item(session: AsyncSession, name: str) -> InspectionItem:
    item = InspectionItem(name=name)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item
