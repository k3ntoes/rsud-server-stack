from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.master.models import RoomItem
from tests.conftest import (
    create_user, auth_header, seed_room, seed_item,
    assign_item_to_room,
)


# ── Android sync — soft-delete tombstone & parent updated_at bump ──


@pytest.mark.asyncio
async def test_unassign_sends_tombstone_to_sync(client: AsyncClient, db_session: AsyncSession):
    """
    Regresi: unassign item dari room kini soft-delete. Sync incremental
    `/api/room-items?since=X` harus mengirim tombstone (is_active=False) sehingga
    Android bisa menghapus item dari mapping lokal — dulu hard-delete membuat
    penghapusan tak terlihat dan jumlah item di room tidak pernah berkurang.
    """
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    room = await seed_room(db_session, "UGD")
    item = await seed_item(db_session, "Kebersihan Tangan")
    await assign_item_to_room(db_session, room.id, item.id)

    before = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    resp = await client.delete(f"/api/rooms/{room.id}/items/{item.id}", headers=headers)
    assert resp.status_code == 204

    resp = await client.get("/api/room-items", params={"since": before}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["room_id"] == room.id
    assert data[0]["item_id"] == item.id
    assert data[0]["is_active"] is False


@pytest.mark.asyncio
async def test_assign_bumps_room_and_item_updated_at(client: AsyncClient, db_session: AsyncSession):
    """Assign item ke room harus menaikkan Room.updated_at & InspectionItem.updated_at."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    room = await seed_room(db_session, "ICU")
    item = await seed_item(db_session, "APD")
    t0_room = room.updated_at
    t0_item = item.updated_at

    await client.post(f"/api/rooms/{room.id}/items", json={"item_id": item.id}, headers=headers)

    await db_session.refresh(room)
    await db_session.refresh(item)
    assert room.updated_at > t0_room
    assert item.updated_at > t0_item


@pytest.mark.asyncio
async def test_unassign_bumps_room_and_item_updated_at(client: AsyncClient, db_session: AsyncSession):
    """Unassign item dari room juga harus menaikkan Room.updated_at & item.updated_at."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    room = await seed_room(db_session, "Poliklinik")
    item = await seed_item(db_session, "Limbah")
    await assign_item_to_room(db_session, room.id, item.id)
    t0_room = room.updated_at
    t0_item = item.updated_at

    resp = await client.delete(f"/api/rooms/{room.id}/items/{item.id}", headers=headers)
    assert resp.status_code == 204

    await db_session.refresh(room)
    await db_session.refresh(item)
    assert room.updated_at > t0_room
    assert item.updated_at > t0_item


@pytest.mark.asyncio
async def test_assign_after_unassign_reactivates_tombstone(client: AsyncClient, db_session: AsyncSession):
    """Re-assign setelah unassign harus reaktivasi tombstone (bukan baris baru)."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    room = await seed_room(db_session, "Rawat Inap")
    item = await seed_item(db_session, "Sterilisasi")
    await assign_item_to_room(db_session, room.id, item.id)

    await client.delete(f"/api/rooms/{room.id}/items/{item.id}", headers=headers)
    resp = await client.post(
        f"/api/rooms/{room.id}/items", json={"item_id": item.id}, headers=headers
    )
    assert resp.status_code == 201
    assert resp.json()["is_active"] is True

    # Hanya satu baris relasi untuk (room, item) — unik constraint tetap terjaga
    result = await db_session.execute(
        select(RoomItem).where(
            RoomItem.room_id == room.id, RoomItem.item_id == item.id
        )
    )
    assert len(result.scalars().all()) == 1


@pytest.mark.asyncio
async def test_list_room_items_excludes_inactive(client: AsyncClient, db_session: AsyncSession):
    """Endpoint per-room (web admin) tidak boleh menampilkan tombstone."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    room = await seed_room(db_session, "UGD")
    item = await seed_item(db_session, "Kebersihan Tangan")
    await assign_item_to_room(db_session, room.id, item.id)
    await client.delete(f"/api/rooms/{room.id}/items/{item.id}", headers=headers)

    resp = await client.get(f"/api/rooms/{room.id}/items", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 0


# ── ADR-0013: sort_order & ordering ──


@pytest.mark.asyncio
async def test_list_items_by_room_ordered_by_sort_order(client: AsyncClient, db_session: AsyncSession):
    """ADR-0013: item per ruangan tampil urut (sort_order ASC, item_id ASC)."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "UGD")
    item_a = await seed_item(db_session, "Tembok")
    item_b = await seed_item(db_session, "Lantai")
    item_c = await seed_item(db_session, "Atap")

    headers = auth_header(admin)
    # Assign via API → sort_order append (0, 1, 2) sesuai urutan assign
    for item in (item_a, item_b, item_c):
        resp = await client.post(
            f"/api/rooms/{room.id}/items", json={"item_id": item.id}, headers=headers
        )
        assert resp.status_code == 201

    # Reorder: Lantai (item_b) → Tembok (item_a) → Atap (item_c)
    resp = await client.put(
        f"/api/rooms/{room.id}/items/reorder",
        json={"item_ids": [item_b.id, item_a.id, item_c.id]},
        headers=headers,
    )
    assert resp.status_code == 200

    resp = await client.get(f"/api/rooms/{room.id}/items", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert [r["item_id"] for r in data] == [item_b.id, item_a.id, item_c.id]
    assert [r["sort_order"] for r in data] == [0, 1, 2]


@pytest.mark.asyncio
async def test_assign_item_appends_to_end_of_room(client: AsyncClient, db_session: AsyncSession):
    """ADR-0013: item baru di-assign harus append di akhir ruangan (max+1)."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "ICU")
    item_a = await seed_item(db_session, "Kebersihan Tangan")
    item_b = await seed_item(db_session, "APD")
    item_c = await seed_item(db_session, "Limbah")

    headers = auth_header(admin)
    for item in (item_a, item_b):
        await client.post(
            f"/api/rooms/{room.id}/items", json={"item_id": item.id}, headers=headers
        )

    resp = await client.post(
        f"/api/rooms/{room.id}/items", json={"item_id": item_c.id}, headers=headers
    )
    assert resp.status_code == 201
    assert resp.json()["sort_order"] == 2  # max(0,1)+1

    data = (await client.get(f"/api/rooms/{room.id}/items", headers=headers)).json()
    assert [r["item_id"] for r in data] == [item_a.id, item_b.id, item_c.id]


@pytest.mark.asyncio
async def test_room_items_sync_includes_sort_order(client: AsyncClient, db_session: AsyncSession):
    """ADR-0013: payload sync `/api/room-items` memuat sort_order untuk Android."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    room = await seed_room(db_session, "UGD")
    item = await seed_item(db_session, "Kebersihan Tangan")
    await assign_item_to_room(db_session, room.id, item.id)

    resp = await client.get("/api/room-items", headers=headers)
    assert resp.status_code == 200
    row = resp.json()["data"][0]
    assert row["room_id"] == room.id
    assert row["item_id"] == item.id
    assert "sort_order" in row
    assert row["sort_order"] == 0


# ── ADR-0013: reorder endpoint (3j5) ──


@pytest.mark.asyncio
async def test_reorder_room_items_updates_order(client: AsyncClient, db_session: AsyncSession):
    """Reorder valid → urutan berubah + response list penuh dalam urutan baru."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    room = await seed_room(db_session, "UGD")
    item_a = await seed_item(db_session, "A")
    item_b = await seed_item(db_session, "B")
    item_c = await seed_item(db_session, "C")
    for item in (item_a, item_b, item_c):
        await assign_item_to_room(db_session, room.id, item.id)

    resp = await client.put(
        f"/api/rooms/{room.id}/items/reorder",
        json={"item_ids": [item_c.id, item_a.id, item_b.id]},
        headers=headers,
    )
    assert resp.status_code == 200
    assert [r["item_id"] for r in resp.json()] == [item_c.id, item_a.id, item_b.id]

    # Persisted: query ulang menunjukkan urutan baru
    data = (await client.get(f"/api/rooms/{room.id}/items", headers=headers)).json()
    assert [r["item_id"] for r in data] == [item_c.id, item_a.id, item_b.id]


@pytest.mark.asyncio
async def test_reorder_room_items_invalid_items_rejected(client: AsyncClient, db_session: AsyncSession):
    """Daftar item_ids harus persis item aktif room — subset/kelebihan ditolak 422."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    room = await seed_room(db_session, "UGD")
    item_a = await seed_item(db_session, "A")
    item_b = await seed_item(db_session, "B")
    await assign_item_to_room(db_session, room.id, item_a.id)
    await assign_item_to_room(db_session, room.id, item_b.id)

    # Subset (item_b dihilangkan)
    resp = await client.put(
        f"/api/rooms/{room.id}/items/reorder",
        json={"item_ids": [item_a.id]},
        headers=headers,
    )
    assert resp.status_code == 422

    # Kelebihan item (item bukan milik room)
    item_c = await seed_item(db_session, "C")
    resp = await client.put(
        f"/api/rooms/{room.id}/items/reorder",
        json={"item_ids": [item_a.id, item_b.id, item_c.id]},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reorder_room_items_sync_bump(client: AsyncClient, db_session: AsyncSession):
    """Reorder harus dibump `updated_at` baris berubah → terlihat di sync `?since=`."""
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    room = await seed_room(db_session, "ICU")
    item_a = await seed_item(db_session, "A")
    item_b = await seed_item(db_session, "B")
    # Assign via API → sort_order 0 dan 1 (distinct)
    for item in (item_a, item_b):
        await client.post(
            f"/api/rooms/{room.id}/items", json={"item_id": item.id}, headers=headers
        )

    before = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    resp = await client.put(
        f"/api/rooms/{room.id}/items/reorder",
        json={"item_ids": [item_b.id, item_a.id]},
        headers=headers,
    )
    assert resp.status_code == 200

    resp = await client.get("/api/room-items", params={"since": before}, headers=headers)
    data = resp.json()["data"]
    assert len(data) == 2  # kedua baris berubah urutannya → keduanya di-bump
    by_item = {r["item_id"]: r for r in data}
    assert by_item[item_a.id]["sort_order"] == 1
    assert by_item[item_b.id]["sort_order"] == 0


@pytest.mark.asyncio
async def test_reorder_room_items_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")
    item = await seed_item(db_session, "Item")
    await assign_item_to_room(db_session, room.id, item.id)

    headers = auth_header(inspector)
    resp = await client.put(
        f"/api/rooms/{room.id}/items/reorder",
        json={"item_ids": [item.id]},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_reorder_room_items_room_not_found(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    resp = await client.put(
        "/api/rooms/999/items/reorder",
        json={"item_ids": [1]},
        headers=headers,
    )
    assert resp.status_code == 404


# ── GET /api/room-items ──


@pytest.mark.asyncio
async def test_list_room_items(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "UGD")
    item_a = await seed_item(db_session, "Kebersihan Tangan")
    item_b = await seed_item(db_session, "APD")
    await assign_item_to_room(db_session, room.id, item_a.id)
    await assign_item_to_room(db_session, room.id, item_b.id)

    headers = auth_header(admin)
    resp = await client.get("/api/room-items", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2
    assert all(r["room_id"] == room.id for r in data)
    item_ids = {r["item_id"] for r in data}
    assert item_a.id in item_ids
    assert item_b.id in item_ids


@pytest.mark.asyncio
async def test_list_room_items_sync(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "ICU")
    item = await seed_item(db_session, "Limbah")
    await assign_item_to_room(db_session, room.id, item.id)

    headers = auth_header(admin)
    # Future timestamp → no results
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    resp = await client.get("/api/room-items", params={"since": future}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_room_items_no_auth(client: AsyncClient):
    resp = await client.get("/api/room-items")
    assert resp.status_code == 401


# ── GET /api/rooms/{room_id}/items ──


@pytest.mark.asyncio
async def test_list_items_by_room(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "Poliklinik")
    item = await seed_item(db_session, "Kebersihan Tangan")
    await assign_item_to_room(db_session, room.id, item.id)

    headers = auth_header(admin)
    resp = await client.get(f"/api/rooms/{room.id}/items", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["room_id"] == room.id
    assert data[0]["item_id"] == item.id


@pytest.mark.asyncio
async def test_list_items_by_room_not_found(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    resp = await client.get("/api/rooms/999/items", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_items_by_room_no_auth(client: AsyncClient):
    resp = await client.get("/api/rooms/1/items")
    assert resp.status_code == 401


# ── GET /api/inspection-items/{item_id}/rooms ──


@pytest.mark.asyncio
async def test_list_rooms_by_item(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room_a = await seed_room(db_session, "UGD")
    room_b = await seed_room(db_session, "ICU")
    item = await seed_item(db_session, "APD")
    await assign_item_to_room(db_session, room_a.id, item.id)
    await assign_item_to_room(db_session, room_b.id, item.id)

    headers = auth_header(admin)
    resp = await client.get(f"/api/inspection-items/{item.id}/rooms", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(r["item_id"] == item.id for r in data)


@pytest.mark.asyncio
async def test_list_rooms_by_item_not_found(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(admin)
    resp = await client.get("/api/inspection-items/999/rooms", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_rooms_by_item_no_auth(client: AsyncClient):
    resp = await client.get("/api/inspection-items/1/rooms")
    assert resp.status_code == 401


# ── POST /api/rooms/{room_id}/items (assign item to room) ──


@pytest.mark.asyncio
async def test_assign_item_to_room(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "Rawat Inap")
    item = await seed_item(db_session, "Kebersihan Tangan")

    headers = auth_header(admin)
    resp = await client.post(
        f"/api/rooms/{room.id}/items",
        json={"item_id": item.id},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["room_id"] == room.id
    assert data["item_id"] == item.id
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_assign_item_to_room_duplicate(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "ICU")
    item = await seed_item(db_session, "APD")
    await assign_item_to_room(db_session, room.id, item.id)

    headers = auth_header(admin)
    resp = await client.post(
        f"/api/rooms/{room.id}/items",
        json={"item_id": item.id},
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_assign_item_to_room_no_item_id(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "UGD")

    headers = auth_header(admin)
    resp = await client.post(
        f"/api/rooms/{room.id}/items",
        json={},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_assign_item_to_room_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")
    item = await seed_item(db_session, "Item")

    headers = auth_header(inspector)
    resp = await client.post(
        f"/api/rooms/{room.id}/items",
        json={"item_id": item.id},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_assign_item_to_room_no_auth(client: AsyncClient):
    resp = await client.post("/api/rooms/1/items", json={"item_id": 1})
    assert resp.status_code == 401


# ── DELETE /api/rooms/{room_id}/items/{item_id} (unassign) ──


@pytest.mark.asyncio
async def test_unassign_item_from_room(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "Poliklinik")
    item = await seed_item(db_session, "Kebersihan Tangan")
    await assign_item_to_room(db_session, room.id, item.id)

    headers = auth_header(admin)
    resp = await client.delete(
        f"/api/rooms/{room.id}/items/{item.id}",
        headers=headers,
    )
    assert resp.status_code == 204

    # Verify it's gone
    list_resp = await client.get(f"/api/rooms/{room.id}/items", headers=headers)
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_unassign_item_from_room_not_found(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")

    headers = auth_header(admin)
    resp = await client.delete("/api/rooms/1/items/999", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unassign_item_from_room_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")
    item = await seed_item(db_session, "Item")

    headers = auth_header(inspector)
    resp = await client.delete(
        f"/api/rooms/{room.id}/items/{item.id}",
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unassign_item_from_room_no_auth(client: AsyncClient):
    resp = await client.delete("/api/rooms/1/items/1")
    assert resp.status_code == 401


# ── POST /api/inspection-items/{item_id}/rooms (assign room to item) ──


@pytest.mark.asyncio
async def test_assign_room_to_item(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "UGD")
    item = await seed_item(db_session, "APD")

    headers = auth_header(admin)
    resp = await client.post(
        f"/api/inspection-items/{item.id}/rooms",
        json={"room_id": room.id},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["room_id"] == room.id
    assert data["item_id"] == item.id


@pytest.mark.asyncio
async def test_assign_room_to_item_no_room_id(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    item = await seed_item(db_session, "Item")

    headers = auth_header(admin)
    resp = await client.post(
        f"/api/inspection-items/{item.id}/rooms",
        json={},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_assign_room_to_item_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    item = await seed_item(db_session, "Item")
    room = await seed_room(db_session, "UGD")

    headers = auth_header(inspector)
    resp = await client.post(
        f"/api/inspection-items/{item.id}/rooms",
        json={"room_id": room.id},
        headers=headers,
    )
    assert resp.status_code == 403


# ── DELETE /api/inspection-items/{item_id}/rooms/{room_id} (unassign via item) ──


@pytest.mark.asyncio
async def test_unassign_room_from_item(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")
    room = await seed_room(db_session, "ICU")
    item = await seed_item(db_session, "Limbah")
    await assign_item_to_room(db_session, room.id, item.id)

    headers = auth_header(admin)
    resp = await client.delete(
        f"/api/inspection-items/{item.id}/rooms/{room.id}",
        headers=headers,
    )
    assert resp.status_code == 204

    # Verify it's gone
    list_resp = await client.get(f"/api/inspection-items/{item.id}/rooms", headers=headers)
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_unassign_room_from_item_not_found(client: AsyncClient, db_session: AsyncSession):
    admin = await create_user(db_session, "admin", "pass", "admin_ppi")

    headers = auth_header(admin)
    resp = await client.delete("/api/inspection-items/1/rooms/999", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unassign_room_from_item_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")
    item = await seed_item(db_session, "Item")

    headers = auth_header(inspector)
    resp = await client.delete(
        f"/api/inspection-items/{item.id}/rooms/{room.id}",
        headers=headers,
    )
    assert resp.status_code == 403
