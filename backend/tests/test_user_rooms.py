from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import (
    create_user, auth_header, seed_room,
    assign_user_to_room,
)


# ── Android sync — soft-delete tombstone & parent updated_at bump ──


@pytest.mark.asyncio
async def test_unassign_user_sends_tombstone_to_sync(client: AsyncClient, db_session: AsyncSession):
    """
    Regresi: unassign user dari room kini soft-delete. Sync bulk
    `/api/auth/user-rooms?since=X` harus mengirim tombstone (is_active=False)
    sehingga Android bisa menghapus room dari daftar petugas.
    """
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")
    await assign_user_to_room(db_session, inspector.id, room.id)

    headers = auth_header(admin)
    before = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    resp = await client.delete(
        f"/api/auth/rooms/{room.id}/users/{inspector.id}", headers=headers
    )
    assert resp.status_code == 204

    resp = await client.get("/api/auth/user-rooms", params={"since": before}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["room_id"] == room.id
    assert data[0]["user_id"] == inspector.id
    assert data[0]["is_active"] is False


@pytest.mark.asyncio
async def test_assign_user_bumps_room_updated_at(client: AsyncClient, db_session: AsyncSession):
    """Assign user ke room harus menaikkan Room.updated_at (sync /rooms ikut berubah)."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "ICU")
    t0 = room.updated_at

    headers = auth_header(admin)
    resp = await client.post(
        f"/api/auth/rooms/{room.id}/users",
        json={"user_id": inspector.id},
        headers=headers,
    )
    assert resp.status_code == 201

    await db_session.refresh(room)
    assert room.updated_at > t0


@pytest.mark.asyncio
async def test_get_my_rooms_excludes_unassigned(client: AsyncClient, db_session: AsyncSession):
    """Setelah unassign, /api/auth/me/rooms tidak lagi mengembalikan room tsb."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")
    await assign_user_to_room(db_session, inspector.id, room.id)

    headers_admin = auth_header(admin)
    resp = await client.delete(
        f"/api/auth/rooms/{room.id}/users/{inspector.id}", headers=headers_admin
    )
    assert resp.status_code == 204

    headers_insp = auth_header(inspector)
    resp = await client.get("/api/auth/me/rooms", headers=headers_insp)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 0


# ── GET /api/auth/me/rooms ──


@pytest.mark.asyncio
async def test_get_my_rooms(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room_a = await seed_room(db_session, "UGD")
    room_b = await seed_room(db_session, "ICU")
    await assign_user_to_room(db_session, inspector.id, room_a.id)
    await assign_user_to_room(db_session, inspector.id, room_b.id)

    headers = auth_header(inspector)
    resp = await client.get("/api/auth/me/rooms", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2
    names = {r["name"] for r in data}
    assert "UGD" in names
    assert "ICU" in names


@pytest.mark.asyncio
async def test_get_my_rooms_empty(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    headers = auth_header(inspector)
    resp = await client.get("/api/auth/me/rooms", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_my_rooms_sync(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "Poliklinik")
    await assign_user_to_room(db_session, inspector.id, room.id)

    headers = auth_header(inspector)
    # Future timestamp → no results
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    resp = await client.get("/api/auth/me/rooms", params={"since": future}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_my_rooms_since_includes_null_updated_at(client: AsyncClient, db_session: AsyncSession):
    """
    Regresi: room ber-`updated_at` NULL (data lama) harus tetap terkirim saat `since`
    dipakai. Dulu `Room.updated_at >= since` mengecualikan NULL → /me/rooms selalu
    kosong di sync pertama Android meski assignment ada. Sama dengan bug yang sudah
    diperbaiki di /rooms dan /inspection-items (master/services.py).
    """
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")
    room.updated_at = None  # simulasikan data lama yang belum backfill
    await db_session.commit()
    await assign_user_to_room(db_session, inspector.id, room.id)

    headers = auth_header(inspector)
    resp = await client.get(
        "/api/auth/me/rooms",
        params={"since": "1970-01-01T00:00:00Z"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "UGD"


@pytest.mark.asyncio
async def test_get_my_rooms_since_filters_by_updated_at(client: AsyncClient, db_session: AsyncSession):
    """Room dengan updated_at lebih lama dari since tetap terfilter benar (NULL-safe)."""
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    old = await seed_room(db_session, "UGD")
    old.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    await db_session.commit()
    await assign_user_to_room(db_session, inspector.id, old.id)

    headers = auth_header(inspector)
    resp = await client.get(
        "/api/auth/me/rooms",
        params={"since": "2026-06-01T00:00:00Z"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_my_rooms_no_auth(client: AsyncClient):
    resp = await client.get("/api/auth/me/rooms")
    assert resp.status_code == 401


# ── GET /api/auth/rooms/{room_id}/users ──


@pytest.mark.asyncio
async def test_list_users_by_room(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    room = await seed_room(db_session, "UGD")
    await assign_user_to_room(db_session, inspector.id, room.id)
    await assign_user_to_room(db_session, supervisor.id, room.id)

    headers = auth_header(admin)
    resp = await client.get(f"/api/auth/rooms/{room.id}/users", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    user_ids = {r["user_id"] for r in data}
    assert inspector.id in user_ids
    assert supervisor.id in user_ids
    assert all(r["room_id"] == room.id for r in data)


@pytest.mark.asyncio
async def test_list_users_by_room_empty(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "ICU")

    headers = auth_header(admin)
    resp = await client.get(f"/api/auth/rooms/{room.id}/users", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_list_users_by_room_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")

    headers = auth_header(inspector)
    resp = await client.get(f"/api/auth/rooms/{room.id}/users", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_users_by_room_no_auth(client: AsyncClient):
    resp = await client.get("/api/auth/rooms/1/users")
    assert resp.status_code == 401


# ── POST /api/auth/rooms/{room_id}/users (assign user to room) ──


@pytest.mark.asyncio
async def test_assign_user_to_room(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "Rawat Inap")

    headers = auth_header(admin)
    resp = await client.post(
        f"/api/auth/rooms/{room.id}/users",
        json={"user_id": inspector.id},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["room_id"] == room.id
    assert data["user_id"] == inspector.id
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_assign_user_to_room_duplicate(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "ICU")
    await assign_user_to_room(db_session, inspector.id, room.id)

    headers = auth_header(admin)
    resp = await client.post(
        f"/api/auth/rooms/{room.id}/users",
        json={"user_id": inspector.id},
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_assign_user_to_room_no_user_id(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "UGD")

    headers = auth_header(admin)
    resp = await client.post(
        f"/api/auth/rooms/{room.id}/users",
        json={},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_assign_user_to_room_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")

    headers = auth_header(inspector)
    resp = await client.post(
        f"/api/auth/rooms/{room.id}/users",
        json={"user_id": inspector.id},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_assign_user_to_room_no_auth(client: AsyncClient):
    resp = await client.post("/api/auth/rooms/1/users", json={"user_id": 1})
    assert resp.status_code == 401


# ── DELETE /api/auth/rooms/{room_id}/users/{user_id} (unassign user from room) ──


@pytest.mark.asyncio
async def test_unassign_user_from_room(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "Poliklinik")
    await assign_user_to_room(db_session, inspector.id, room.id)

    headers = auth_header(admin)
    resp = await client.delete(
        f"/api/auth/rooms/{room.id}/users/{inspector.id}",
        headers=headers,
    )
    assert resp.status_code == 204

    # Verify it's gone
    list_resp = await client.get(f"/api/auth/rooms/{room.id}/users", headers=headers)
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_unassign_user_from_room_not_found(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")

    headers = auth_header(admin)
    resp = await client.delete("/api/auth/rooms/1/users/999", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unassign_user_from_room_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")

    headers = auth_header(inspector)
    resp = await client.delete(
        f"/api/auth/rooms/{room.id}/users/{inspector.id}",
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unassign_user_from_room_no_auth(client: AsyncClient):
    resp = await client.delete("/api/auth/rooms/1/users/1")
    assert resp.status_code == 401


# ── GET /api/auth/users/{user_id}/rooms ──


@pytest.mark.asyncio
async def test_list_rooms_by_user(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room_a = await seed_room(db_session, "UGD")
    room_b = await seed_room(db_session, "ICU")
    await assign_user_to_room(db_session, inspector.id, room_a.id)
    await assign_user_to_room(db_session, inspector.id, room_b.id)

    headers = auth_header(admin)
    resp = await client.get(f"/api/auth/users/{inspector.id}/rooms", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(r["user_id"] == inspector.id for r in data)
    room_ids = {r["room_id"] for r in data}
    assert room_a.id in room_ids
    assert room_b.id in room_ids


@pytest.mark.asyncio
async def test_list_rooms_by_user_empty(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")

    headers = auth_header(admin)
    resp = await client.get(f"/api/auth/users/{inspector.id}/rooms", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_list_rooms_by_user_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")

    headers = auth_header(inspector)
    resp = await client.get(f"/api/auth/users/{inspector.id}/rooms", headers=headers)
    assert resp.status_code == 403


# ── POST /api/auth/users/{user_id}/rooms (assign room to user) ──


@pytest.mark.asyncio
async def test_assign_room_to_user(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "Rawat Inap")

    headers = auth_header(admin)
    resp = await client.post(
        f"/api/auth/users/{inspector.id}/rooms",
        json={"room_id": room.id},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["room_id"] == room.id
    assert data["user_id"] == inspector.id


@pytest.mark.asyncio
async def test_assign_room_to_user_no_room_id(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")

    headers = auth_header(admin)
    resp = await client.post(
        f"/api/auth/users/{inspector.id}/rooms",
        json={},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_assign_room_to_user_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")

    headers = auth_header(inspector)
    resp = await client.post(
        f"/api/auth/users/{inspector.id}/rooms",
        json={"room_id": room.id},
        headers=headers,
    )
    assert resp.status_code == 403


# ── DELETE /api/auth/users/{user_id}/rooms/{room_id} (unassign room from user) ──


@pytest.mark.asyncio
async def test_unassign_room_from_user(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "ICU")
    await assign_user_to_room(db_session, inspector.id, room.id)

    headers = auth_header(admin)
    resp = await client.delete(
        f"/api/auth/users/{inspector.id}/rooms/{room.id}",
        headers=headers,
    )
    assert resp.status_code == 204

    # Verify it's gone
    list_resp = await client.get(f"/api/auth/users/{inspector.id}/rooms", headers=headers)
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_unassign_room_from_user_not_found(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")

    headers = auth_header(admin)
    resp = await client.delete(
        f"/api/auth/users/{inspector.id}/rooms/999",
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unassign_room_from_user_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")

    headers = auth_header(inspector)
    resp = await client.delete(
        f"/api/auth/users/{inspector.id}/rooms/{room.id}",
        headers=headers,
    )
    assert resp.status_code == 403


# ── GET /api/auth/users includes room_ids ──


@pytest.mark.asyncio
async def test_list_users_includes_room_ids(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room_a = await seed_room(db_session, "UGD")
    room_b = await seed_room(db_session, "ICU")
    await assign_user_to_room(db_session, inspector.id, room_a.id)
    await assign_user_to_room(db_session, inspector.id, room_b.id)

    headers = auth_header(admin)
    resp = await client.get("/api/auth/users", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    items = data["items"]
    insp_data = next(u for u in items if u["id"] == inspector.id)
    assert "room_ids" in insp_data
    assert sorted(insp_data["room_ids"]) == sorted([room_a.id, room_b.id])

    # Admin with no rooms should have empty list
    admin_data = next(u for u in items if u["id"] == admin.id)
    assert admin_data["room_ids"] == []
