import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.modules.auth.models import User
from tests.conftest import create_user, auth_header


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    await create_user(db_session, "testuser", "testpass", "inspector")
    resp = await client.post("/api/auth/login", json={"username": "testuser", "password": "testpass"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == "testuser"
    assert data["user"]["role"] == "inspector"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, db_session: AsyncSession):
    await create_user(db_session, "testuser", "testpass", "inspector")
    resp = await client.post("/api/auth/login", json={"username": "testuser", "password": "wrong"})
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.text


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient, db_session: AsyncSession):
    resp = await client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session: AsyncSession):
    user = await create_user(db_session, "inactive", "pass", "inspector")
    user.is_active = False
    await db_session.commit()
    resp = await client.post("/api/auth/login", json={"username": "inactive", "password": "pass"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, db_session: AsyncSession):
    user = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(user)
    resp = await client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"
    assert resp.json()["role"] == "admin_ppi"


@pytest.mark.asyncio
async def test_me_no_token(client: AsyncClient):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(client: AsyncClient):
    resp = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_wrong_token_type(client: AsyncClient, db_session: AsyncSession):
    user = await create_user(db_session, "u", "p", "inspector")
    # Create a refresh token, try using it as access token
    from app.core.security import create_refresh_token
    token = create_refresh_token({"sub": str(user.id)})
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_cookie(client: AsyncClient, db_session: AsyncSession):
    # Login to get refresh_token cookie
    await create_user(db_session, "u", "p", "inspector")
    login_resp = await client.post("/api/auth/login", json={"username": "u", "password": "p"})
    assert login_resp.status_code == 200

    refresh_token = login_resp.cookies.get("refresh_token")
    assert refresh_token is not None

    resp = await client.post("/api/auth/refresh")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    # Token rotation: new refresh_token should be set
    new_cookie = resp.cookies.get("refresh_token")
    assert new_cookie is not None
    assert new_cookie != refresh_token


@pytest.mark.asyncio
async def test_refresh_no_cookie(client: AsyncClient):
    resp = await client.post("/api/auth/refresh")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, db_session: AsyncSession):
    await create_user(db_session, "u", "p", "inspector")
    login_resp = await client.post("/api/auth/login", json={"username": "u", "password": "p"})
    assert login_resp.status_code == 200

    resp = await client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out"

    # Old refresh_token no longer works
    old_cookie = login_resp.cookies.get("refresh_token")
    client.cookies.set("refresh_token", old_cookie)
    refresh_resp = await client.post("/api/auth/refresh")
    assert refresh_resp.status_code == 401
