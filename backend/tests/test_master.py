import pytest
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
    assert len(data) == 2
    names = [r["name"] for r in data]
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
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_room_non_admin_forbidden(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "inspector", "pass", "inspector")
    headers = auth_header(inspector)
    resp = await client.post("/api/rooms", json={"name": "ICU"}, headers=headers)
    assert resp.status_code == 403

    resp = await client.get("/api/rooms", headers=headers)
    assert resp.status_code == 403


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
    assert len(resp.json()) == 2


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
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_item_non_admin_forbidden(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "inspector", "pass", "inspector")
    headers = auth_header(inspector)
    resp = await client.post("/api/inspection-items", json={"name": "Item"}, headers=headers)
    assert resp.status_code == 403
