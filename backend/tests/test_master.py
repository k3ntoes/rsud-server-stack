import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_user, auth_header, seed_room, seed_item


@pytest.mark.asyncio
async def test_create_room(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    resp = await client.post("/api/rooms", json={"name": "ICU"}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "ICU"
    assert resp.json()["is_active"] is True


@pytest.mark.asyncio
async def test_list_rooms(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    await seed_room(db_session, "UGD")
    await seed_room(db_session, "ICU")
    headers = auth_header(admin)
    resp = await client.get("/api/rooms", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    names = [r["name"] for r in data["items"]]
    assert "UGD" in names
    assert "ICU" in names


@pytest.mark.asyncio
async def test_create_room_duplicate(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    await client.post("/api/rooms", json={"name": "ICU"}, headers=headers)
    resp = await client.post("/api/rooms", json={"name": "ICU"}, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_room_by_id(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "Poliklinik")
    headers = auth_header(admin)
    resp = await client.get(f"/api/rooms/{room.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Poliklinik"


@pytest.mark.asyncio
async def test_get_room_not_found(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    resp = await client.get("/api/rooms/999", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_room(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "Old Name")
    headers = auth_header(admin)
    resp = await client.put(f"/api/rooms/{room.id}", json={"name": "New Name"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_room(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "To Delete")
    headers = auth_header(admin)
    resp = await client.delete(f"/api/rooms/{room.id}", headers=headers)
    assert resp.status_code == 204

    # Should no longer appear in list
    list_resp = await client.get("/api/rooms", headers=headers)
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_room_non_admin_forbidden(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "inspector", "pass", "inspector")
    headers = auth_header(inspector)
    resp = await client.post("/api/rooms", json={"name": "ICU"}, headers=headers)
    assert resp.status_code == 403

    # GET is now public for any authenticated user (Phase 8 — Android sync)
    resp = await client.get("/api/rooms", headers=headers)
    assert resp.status_code == 200
    assert "items" in resp.json()


# ── Android sync — `since` filter (NULL updated_at regression) ──


@pytest.mark.asyncio
async def test_list_rooms_since_includes_null_updated_at(client: AsyncClient, db_session: AsyncSession):
    """
    Regresi: baris ber-`updated_at` NULL (data lama sebelum kolom ini diisi)
    harus tetap terkirim saat `since` dipakai. Dulu `updated_at >= since`
    mengecualikan NULL (NULL >= x = NULL di SQL) → sync pertama Android selalu
    kosong meski data ada. Lihat docs/API-contract-* untuk konteks.
    """
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    room = await seed_room(db_session, "UGD")
    room.updated_at = None  # simulasikan data lama yang belum backfill
    await db_session.commit()

    resp = await client.get("/api/rooms?since=1970-01-01T00:00:00Z", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data  # mode sync (unpaginated) saat since dipakai
    names = [r["name"] for r in data["data"]]
    assert "UGD" in names


@pytest.mark.asyncio
async def test_list_items_since_includes_null_updated_at(client: AsyncClient, db_session: AsyncSession):
    """Regresi yang sama untuk inspection-items (NULL updated_at harus ikut terkirim)."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    item = await seed_item(db_session, "Kebersihan Tangan")
    item.updated_at = None
    await db_session.commit()

    resp = await client.get("/api/inspection-items?since=1970-01-01T00:00:00Z", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    names = [i["name"] for i in data["data"]]
    assert "Kebersihan Tangan" in names


@pytest.mark.asyncio
async def test_list_rooms_since_filters_by_updated_at(client: AsyncClient, db_session: AsyncSession):
    """Baris dengan updated_at yang lebih baru dari since tetap terfilter dengan benar."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    old = await seed_room(db_session, "UGD")
    old.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    new = await seed_room(db_session, "ICU")
    new.updated_at = datetime(2026, 7, 1, tzinfo=timezone.utc)
    await db_session.commit()

    resp = await client.get("/api/rooms?since=2026-06-01T00:00:00Z", headers=headers)
    names = [r["name"] for r in resp.json()["data"]]
    assert "ICU" in names
    assert "UGD" not in names


# ── Inspection Items ──


@pytest.mark.asyncio
async def test_create_item(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    resp = await client.post("/api/inspection-items", json={"name": "Kebersihan Tangan"}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Kebersihan Tangan"


@pytest.mark.asyncio
async def test_list_items(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    await seed_item(db_session, "Item A")
    await seed_item(db_session, "Item B")
    headers = auth_header(admin)
    resp = await client.get("/api/inspection-items", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_create_item_duplicate(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    await client.post("/api/inspection-items", json={"name": "APD"}, headers=headers)
    resp = await client.post("/api/inspection-items", json={"name": "APD"}, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_item(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    item = await seed_item(db_session, "Old Item")
    headers = auth_header(admin)
    resp = await client.put(f"/api/inspection-items/{item.id}", json={"name": "New Item"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Item"


@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    item = await seed_item(db_session, "To Delete")
    headers = auth_header(admin)
    resp = await client.delete(f"/api/inspection-items/{item.id}", headers=headers)
    assert resp.status_code == 204

    list_resp = await client.get("/api/inspection-items", headers=headers)
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_item_non_admin_forbidden(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "inspector", "pass", "inspector")
    headers = auth_header(inspector)
    resp = await client.post("/api/inspection-items", json={"name": "Item"}, headers=headers)
    assert resp.status_code == 403

    # GET is now public for any authenticated user (Phase 8 — Android sync)
    resp = await client.get("/api/inspection-items", headers=headers)
    assert resp.status_code == 200
    assert "items" in resp.json()
