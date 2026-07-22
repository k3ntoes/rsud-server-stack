from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_user, auth_header, seed_room, seed_item


def _submit_body(room_id: int, item_ids: list[int]) -> dict:
    """Helper: build a valid inspection submit body."""
    return {
        "room_id": room_id,
        "local_timestamp": datetime.now(timezone.utc).isoformat(),
        "business_date": date.today().isoformat(),
        "details": [
            {"item_id": iid, "score": 2} for iid in item_ids
        ],
    }


@pytest.mark.asyncio
async def test_submit_inspection(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "UGD")
    item = await seed_item(db_session, "Kebersihan Tangan")
    headers = auth_header(inspector)

    body = _submit_body(room.id, [item.id])
    resp = await client.post("/api/inspections", json=body, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "PENDING"
    assert data["room_id"] == room.id
    assert len(data["details"]) == 1
    assert data["details"][0]["item_name_snapshot"] == "Kebersihan Tangan"
    assert data["details"][0]["score"] == 2


@pytest.mark.asyncio
async def test_submit_inspection_duplicate(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "ICU")
    item = await seed_item(db_session, "APD")
    headers = auth_header(inspector)

    body = _submit_body(room.id, [item.id])
    await client.post("/api/inspections", json=body, headers=headers)
    # Same room + same timestamp = duplicate (unique constraint)
    resp = await client.post("/api/inspections", json=body, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_inspections_as_supervisor(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    room = await seed_room(db_session, "Rawat Inap")
    item = await seed_item(db_session, "Item A")
    headers = auth_header(inspector)

    body = _submit_body(room.id, [item.id])
    await client.post("/api/inspections", json=body, headers=headers)

    sup_headers = auth_header(supervisor)
    resp = await client.get("/api/inspections", headers=sup_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["detail_count"] == 1


@pytest.mark.asyncio
async def test_list_inspections_as_inspector_forbidden(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    headers = auth_header(inspector)
    resp = await client.get("/api/inspections", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_inspection_detail(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    room = await seed_room(db_session, "Poliklinik")
    items = [await seed_item(db_session, f"Item {i}") for i in range(2)]
    headers = auth_header(inspector)

    body = _submit_body(room.id, [i.id for i in items])
    create_resp = await client.post("/api/inspections", json=body, headers=headers)
    insp_id = create_resp.json()["id"]

    sup_headers = auth_header(supervisor)
    resp = await client.get(f"/api/inspections/{insp_id}", headers=sup_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["details"]) == 2


@pytest.mark.asyncio
async def test_approve_inspection(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    room = await seed_room(db_session, "UGD")
    item = await seed_item(db_session, "APD")
    headers = auth_header(inspector)

    body = _submit_body(room.id, [item.id])
    create_resp = await client.post("/api/inspections", json=body, headers=headers)
    insp_id = create_resp.json()["id"]

    sup_headers = auth_header(supervisor)
    resp = await client.post(f"/api/inspections/{insp_id}/approve", headers=sup_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_reject_inspection(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    room = await seed_room(db_session, "ICU")
    item = await seed_item(db_session, "Limbah")
    headers = auth_header(inspector)

    body = _submit_body(room.id, [item.id])
    create_resp = await client.post("/api/inspections", json=body, headers=headers)
    insp_id = create_resp.json()["id"]

    sup_headers = auth_header(supervisor)
    resp = await client.post(
        f"/api/inspections/{insp_id}/reject",
        json={"rejection_reason": "Foto tidak lengkap"},
        headers=sup_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert data["rejection_reason"] == "Foto tidak lengkap"


@pytest.mark.asyncio
async def test_approve_already_approved(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    room = await seed_room(db_session, "UGD")
    item = await seed_item(db_session, "Item X")
    headers = auth_header(inspector)

    body = _submit_body(room.id, [item.id])
    create_resp = await client.post("/api/inspections", json=body, headers=headers)
    insp_id = create_resp.json()["id"]

    sup_headers = auth_header(supervisor)
    await client.post(f"/api/inspections/{insp_id}/approve", headers=sup_headers)
    # Approving again should fail
    resp = await client.post(f"/api/inspections/{insp_id}/approve", headers=sup_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_inspector_cannot_approve(client: AsyncClient, db_session: AsyncSession):
    inspector1 = await create_user(db_session, "insp1", "pass", "inspector")
    inspector2 = await create_user(db_session, "insp2", "pass", "inspector")
    room = await seed_room(db_session, "Room")
    item = await seed_item(db_session, "Item")
    headers = auth_header(inspector1)

    body = _submit_body(room.id, [item.id])
    create_resp = await client.post("/api/inspections", json=body, headers=headers)
    insp_id = create_resp.json()["id"]

    # Another inspector tries to approve — 403 (not supervisor)
    other_headers = auth_header(inspector2)
    resp = await client.post(f"/api/inspections/{insp_id}/approve", headers=other_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_inspection_not_found(client: AsyncClient, db_session: AsyncSession):
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    headers = auth_header(supervisor)
    resp = await client.get("/api/inspections/999", headers=headers)
    assert resp.status_code == 404
