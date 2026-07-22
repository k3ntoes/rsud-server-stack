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


# ── User CRUD (admin only) ──


@pytest.mark.asyncio
async def test_list_users_as_admin(client: AsyncClient, db_session: AsyncSession):
    """Admin can list all users."""
    await create_user(db_session, "insp1", "pass", "inspector")
    await create_user(db_session, "insp2", "pass", "inspector")
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")

    headers = auth_header(admin)
    resp = await client.get("/api/auth/users", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    usernames = {u["username"] for u in data}
    assert "insp1" in usernames
    assert "insp2" in usernames
    assert "admin" in usernames


@pytest.mark.asyncio
async def test_list_users_as_inspector_forbidden(client: AsyncClient, db_session: AsyncSession):
    """Non-admin gets 403."""
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    headers = auth_header(inspector)
    resp = await client.get("/api/auth/users", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_users_no_auth(client: AsyncClient):
    """No token → 401."""
    resp = await client.get("/api/auth/users")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient, db_session: AsyncSession):
    """Admin creates a new inspector."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)

    resp = await client.post(
        "/api/auth/users",
        json={"username": "newinspector", "password": "secret123", "role": "inspector"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newinspector"
    assert data["role"] == "inspector"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_user_duplicate(client: AsyncClient, db_session: AsyncSession):
    """Duplicate username → 409."""
    await create_user(db_session, "existing", "pass", "inspector")
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)

    resp = await client.post(
        "/api/auth/users",
        json={"username": "existing", "password": "secret", "role": "inspector"},
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_user_as_inspector_forbidden(client: AsyncClient, db_session: AsyncSession):
    """Non-admin cannot create users."""
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    headers = auth_header(inspector)

    resp = await client.post(
        "/api/auth/users",
        json={"username": "hacker", "password": "p", "role": "admin_ppi"},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_user_role(client: AsyncClient, db_session: AsyncSession):
    """Admin can change a user's role."""
    user = await create_user(db_session, "insp", "pass", "inspector")
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)

    resp = await client.put(
        f"/api/auth/users/{user.id}",
        json={"role": "supervisor"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "supervisor"


@pytest.mark.asyncio
async def test_update_user_deactivate(client: AsyncClient, db_session: AsyncSession):
    """Admin can deactivate a user."""
    user = await create_user(db_session, "insp", "pass", "inspector")
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)

    resp = await client.put(
        f"/api/auth/users/{user.id}",
        json={"is_active": False},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_update_user_nonexistent(client: AsyncClient, db_session: AsyncSession):
    """Updating nonexistent user → 404."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)

    resp = await client.put(
        "/api/auth/users/99999",
        json={"username": "ghost"},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_soft_delete(client: AsyncClient, db_session: AsyncSession):
    """Delete user = soft-deactivate (is_active=False)."""
    user = await create_user(db_session, "to_delete", "pass", "inspector")
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)

    resp = await client.delete(f"/api/auth/users/{user.id}", headers=headers)
    assert resp.status_code == 204

    # Verify user is no longer active
    user_list_resp = await client.get("/api/auth/users", headers=headers)
    users = user_list_resp.json()
    deleted = next(u for u in users if u["id"] == user.id)
    assert deleted["is_active"] is False


@pytest.mark.asyncio
async def test_delete_user_nonexistent(client: AsyncClient, db_session: AsyncSession):
    """Deleting nonexistent user → 404."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)

    resp = await client.delete("/api/auth/users/99999", headers=headers)
    assert resp.status_code == 404


# ── Change Password ──


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient, db_session: AsyncSession):
    """User can change password with correct old password."""
    user = await create_user(db_session, "user", "oldpass", "inspector")
    headers = auth_header(user)

    resp = await client.post(
        "/api/auth/change-password",
        json={"old_password": "oldpass", "new_password": "newpass123"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Password changed successfully"


@pytest.mark.asyncio
async def test_change_password_wrong_old(client: AsyncClient, db_session: AsyncSession):
    """Wrong old password → 400."""
    user = await create_user(db_session, "user", "realpass", "inspector")
    headers = auth_header(user)

    resp = await client.post(
        "/api/auth/change-password",
        json={"old_password": "wrongpass", "new_password": "newpass123"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "Current password is incorrect" in resp.text


@pytest.mark.asyncio
async def test_change_password_no_auth(client: AsyncClient):
    """No token → 401."""
    resp = await client.post(
        "/api/auth/change-password",
        json={"old_password": "x", "new_password": "y"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_change_password_login_with_new_password(client: AsyncClient, db_session: AsyncSession):
    """Old password rejected after change; new password works."""
    user = await create_user(db_session, "changeme", "oldpw", "inspector")
    headers = auth_header(user)

    # Change password
    await client.post(
        "/api/auth/change-password",
        json={"old_password": "oldpw", "new_password": "newpw"},
        headers=headers,
    )

    # Old password no longer works
    resp_old = await client.post("/api/auth/login", json={"username": "changeme", "password": "oldpw"})
    assert resp_old.status_code == 401

    # New password works
    resp_new = await client.post("/api/auth/login", json={"username": "changeme", "password": "newpw"})
    assert resp_new.status_code == 200


# ── Admin Reset Password ──


@pytest.mark.asyncio
async def test_admin_reset_password_success(client: AsyncClient, db_session: AsyncSession):
    """Admin resets a user's password; old sessions revoked, old password rejected."""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select
    from app.modules.auth.models import UserSession

    user = await create_user(db_session, "forgotpass", "oldpw", "inspector")
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)

    # Create a session for the user (simulate being logged in)
    from app.core.security import create_refresh_token
    session = UserSession(
        user_id=user.id,
        refresh_token=create_refresh_token({"sub": str(user.id), "jti": "test-jti-1"}),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_active=True,
    )
    db_session.add(session)
    await db_session.commit()

    resp = await client.put(
        f"/api/auth/users/{user.id}/reset-password",
        json={"new_password": "reset123"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Password reset successfully"

    # All old sessions revoked (check before any new login creates sessions)
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.is_active == True,
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 0, "Old sessions should be revoked"

    # Old password no longer works
    resp_old = await client.post("/api/auth/login", json={"username": "forgotpass", "password": "oldpw"})
    assert resp_old.status_code == 401

    # New password works (creates new session — that's fine)
    resp_new = await client.post("/api/auth/login", json={"username": "forgotpass", "password": "reset123"})
    assert resp_new.status_code == 200


@pytest.mark.asyncio
async def test_admin_reset_password_nonexistent_user(client: AsyncClient, db_session: AsyncSession):
    """Nonexistent user → 404."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)

    resp = await client.put(
        "/api/auth/users/99999/reset-password",
        json={"new_password": "reset123"},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_reset_password_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    """Non-admin cannot reset passwords → 403."""
    user = await create_user(db_session, "target", "pass", "inspector")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    headers = auth_header(inspector)

    resp = await client.put(
        f"/api/auth/users/{user.id}/reset-password",
        json={"new_password": "reset123"},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_reset_password_no_auth(client: AsyncClient, db_session: AsyncSession):
    """No token → 401."""
    resp = await client.put(
        "/api/auth/users/1/reset-password",
        json={"new_password": "reset123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_reset_password_too_short(client: AsyncClient, db_session: AsyncSession):
    """Password less than 6 characters → 422."""
    user = await create_user(db_session, "target", "pass", "inspector")
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)

    resp = await client.put(
        f"/api/auth/users/{user.id}/reset-password",
        json={"new_password": "abc"},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_admin_reset_password_by_supervisor_forbidden(client: AsyncClient, db_session: AsyncSession):
    """Supervisor cannot reset passwords → 403."""
    user = await create_user(db_session, "target", "pass", "inspector")
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    headers = auth_header(supervisor)

    resp = await client.put(
        f"/api/auth/users/{user.id}/reset-password",
        json={"new_password": "reset123"},
        headers=headers,
    )
    assert resp.status_code == 403
