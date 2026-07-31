from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import (
    create_user, auth_header, seed_room, seed_item,
    assign_item_to_room, assign_user_to_room,
)


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
    await assign_user_to_room(db_session, inspector.id, room.id)
    await assign_item_to_room(db_session, room.id, item.id)
    headers = auth_header(inspector)

    body = _submit_body(room.id, [item.id])
    resp = await client.post("/api/inspections", json=body, headers=headers)
    assert resp.status_code == 201, resp.text
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
    await assign_user_to_room(db_session, inspector.id, room.id)
    await assign_item_to_room(db_session, room.id, item.id)
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
    await assign_user_to_room(db_session, inspector.id, room.id)
    await assign_user_to_room(db_session, supervisor.id, room.id)
    await assign_item_to_room(db_session, room.id, item.id)
    headers = auth_header(inspector)

    body = _submit_body(room.id, [item.id])
    await client.post("/api/inspections", json=body, headers=headers)

    sup_headers = auth_header(supervisor)
    resp = await client.get("/api/inspections", headers=sup_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["detail_count"] == 1


@pytest.mark.asyncio
async def test_list_inspections_as_inspector_allowed(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    headers = auth_header(inspector)
    resp = await client.get("/api/inspections", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_inspection_detail(client: AsyncClient, db_session: AsyncSession):
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    room = await seed_room(db_session, "Poliklinik")
    items = [await seed_item(db_session, f"Item {i}") for i in range(2)]
    await assign_user_to_room(db_session, inspector.id, room.id)
    await assign_user_to_room(db_session, supervisor.id, room.id)
    for item in items:
        await assign_item_to_room(db_session, room.id, item.id)
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
    await assign_user_to_room(db_session, inspector.id, room.id)
    await assign_item_to_room(db_session, room.id, item.id)
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
    await assign_user_to_room(db_session, inspector.id, room.id)
    await assign_item_to_room(db_session, room.id, item.id)
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
    await assign_user_to_room(db_session, inspector.id, room.id)
    await assign_item_to_room(db_session, room.id, item.id)
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
    await assign_user_to_room(db_session, inspector1.id, room.id)
    await assign_item_to_room(db_session, room.id, item.id)
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


# ── Replace Photo (PUT /api/inspections/{id}/photos/{photoId}, ADR-0012) ──


def _submit_body_with_photo(room_id: int, item_ids: list[int]) -> dict:
    """Submit body with a photo on the first item (file_name is a stub)."""
    body = _submit_body(room_id, item_ids)
    body["details"][0]["photos"] = [
        {"file_name": "old-photo.jpg", "sort_order": 0}
    ]
    return body


async def _submit_inspection_with_photo(
    client: AsyncClient, db_session: AsyncSession, role: str = "inspector"
) -> tuple[dict, dict]:
    """Create inspection with one photo; returns (auth_headers, created_json)."""
    inspector = await create_user(db_session, "insp", "pass", role)
    room = await seed_room(db_session, "UGD")
    item = await seed_item(db_session, "Kebersihan Tangan")
    await assign_user_to_room(db_session, inspector.id, room.id)
    await assign_item_to_room(db_session, room.id, item.id)
    headers = auth_header(inspector)
    resp = await client.post(
        "/api/inspections", json=_submit_body_with_photo(room.id, [item.id]), headers=headers
    )
    assert resp.status_code == 201, resp.text
    return headers, resp.json()


@pytest.mark.asyncio
async def test_replace_inspection_photo(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, tmp_path
):
    """Owner replaces a photo: 200, new file name, sort_order unchanged, old file removed."""
    from app.config import settings
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    headers, created = await _submit_inspection_with_photo(client, db_session)
    insp_id = created["id"]
    photo = created["details"][0]["photos"][0]
    photo_id = photo["id"]
    assert photo["photo_file_name"] == "old-photo.jpg"

    # Simulate old file existing on disk
    old_path = tmp_path / "old-photo.jpg"
    old_path.write_bytes(b"old-image-bytes")

    resp = await client.put(
        f"/api/inspections/{insp_id}/photos/{photo_id}",
        files={"file": ("new-photo.jpg", b"new-image-bytes", "image/jpeg")},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"] == photo_id
    assert data["photo_file_name"] != "old-photo.jpg"
    assert data["photo_file_name"].endswith(".jpg")
    assert data["thumbnail_file_name"] is None
    assert data["sort_order"] == 0

    # Old file deleted from disk after commit
    assert not old_path.exists()
    # New file exists on disk
    assert (tmp_path / data["photo_file_name"]).exists()


@pytest.mark.asyncio
async def test_replace_inspection_photo_as_supervisor(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, tmp_path
):
    """Supervisor can replace a photo of an inspection owned by someone else."""
    from app.config import settings
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    _, created = await _submit_inspection_with_photo(client, db_session)
    insp_id = created["id"]
    photo_id = created["details"][0]["photos"][0]["id"]

    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    sup_headers = auth_header(supervisor)
    resp = await client.put(
        f"/api/inspections/{insp_id}/photos/{photo_id}",
        files={"file": ("new.jpg", b"bytes", "image/jpeg")},
        headers=sup_headers,
    )
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_replace_inspection_photo_forbidden(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, tmp_path
):
    """Another inspector (not owner) cannot replace → 403 FORBIDDEN."""
    from app.config import settings
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    _, created = await _submit_inspection_with_photo(client, db_session)
    insp_id = created["id"]
    photo_id = created["details"][0]["photos"][0]["id"]

    other = await create_user(db_session, "other", "pass", "inspector")
    other_headers = auth_header(other)
    resp = await client.put(
        f"/api/inspections/{insp_id}/photos/{photo_id}",
        files={"file": ("new.jpg", b"bytes", "image/jpeg")},
        headers=other_headers,
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_replace_inspection_photo_not_found(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, tmp_path
):
    """Nonexistent inspection or photo → 404 PHOTO_NOT_FOUND."""
    from app.config import settings
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    headers, created = await _submit_inspection_with_photo(client, db_session)
    insp_id = created["id"]
    photo_id = created["details"][0]["photos"][0]["id"]

    # Inspection doesn't exist
    resp = await client.put(
        f"/api/inspections/99999/photos/{photo_id}",
        files={"file": ("new.jpg", b"bytes", "image/jpeg")},
        headers=headers,
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "PHOTO_NOT_FOUND"

    # Photo doesn't belong to inspection
    resp2 = await client.put(
        f"/api/inspections/{insp_id}/photos/99999",
        files={"file": ("new.jpg", b"bytes", "image/jpeg")},
        headers=headers,
    )
    assert resp2.status_code == 404
    assert resp2.json()["code"] == "PHOTO_NOT_FOUND"


@pytest.mark.asyncio
async def test_replace_inspection_photo_missing_file(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, tmp_path
):
    """No file in multipart → 422 MISSING_FILE."""
    from app.config import settings
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    headers, created = await _submit_inspection_with_photo(client, db_session)
    insp_id = created["id"]
    photo_id = created["details"][0]["photos"][0]["id"]

    resp = await client.put(
        f"/api/inspections/{insp_id}/photos/{photo_id}", headers=headers
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "MISSING_FILE"


@pytest.mark.asyncio
async def test_replace_inspection_photo_too_large(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, tmp_path
):
    """File over 10MB → 413 FILE_TOO_LARGE (safety net from save_upload)."""
    from app.config import settings
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    headers, created = await _submit_inspection_with_photo(client, db_session)
    insp_id = created["id"]
    photo_id = created["details"][0]["photos"][0]["id"]

    big = b"x" * (10 * 1024 * 1024 + 1)
    resp = await client.put(
        f"/api/inspections/{insp_id}/photos/{photo_id}",
        files={"file": ("big.jpg", big, "image/jpeg")},
        headers=headers,
    )
    assert resp.status_code == 413
    assert resp.json()["code"] == "FILE_TOO_LARGE"
