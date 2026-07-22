"""
Tests for analytics endpoints.

Covers:
- GET /api/analytics/lowest-rooms (basic, empty, filter, role, limit)
- GET /api/analytics/top-issues (basic, empty, filter, role)
"""

from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_user, auth_header, seed_room, seed_item
from app.modules.inspection.models import Inspection, InspectionDetail
from app.modules.background.services import recalculate_analytics


async def _seed_approved_inspection(
    db_session: AsyncSession,
    room_id: int,
    inspector_id: int,
    item_ids: list[int],
    scores: list[int],
    business_date: date | None = None,
) -> int:
    """Create an APPROVED inspection with details, then recalculate analytics.

    item_ids and scores must be same length — passed item_ids must reference
    existing entries in the inspection_items table (use seed_item() to create).
    Returns the inspection_id.
    """
    insp = Inspection(
        room_id=room_id,
        inspector_id=inspector_id,
        status="APPROVED",
        business_date=business_date or date.today(),
        local_timestamp=datetime.now(timezone.utc),
    )
    for iid, score in zip(item_ids, scores):
        insp.details.append(InspectionDetail(
            item_id=iid,
            item_name_snapshot=f"Item {iid}",
            score=score,
        ))
    db_session.add(insp)
    await db_session.commit()
    await db_session.refresh(insp)

    await recalculate_analytics(db_session, insp.id)
    return insp.id


# ── lowest-rooms ──


@pytest.mark.asyncio
async def test_lowest_rooms_ordered_by_score_asc(
    client: AsyncClient, db_session: AsyncSession,
):
    """Returns rooms sorted ascending by score_pct."""
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room_low = await seed_room(db_session, "Ruang Rendah")   # 0/2 → 0%
    room_high = await seed_room(db_session, "Ruang Tinggi")  # 4/4 → 100%
    item = await seed_item(db_session, "Item")

    await _seed_approved_inspection(
        db_session, room_low.id, inspector.id, [item.id], [0],
    )
    await _seed_approved_inspection(
        db_session, room_high.id, inspector.id, [item.id, item.id], [2, 2],
    )

    headers = auth_header(supervisor)
    resp = await client.get("/api/analytics/lowest-rooms?limit=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["room_id"] == room_low.id
    assert data[0]["score_pct"] == 0.0
    assert data[0]["inspection_count"] == 1
    assert data[1]["room_id"] == room_high.id
    assert data[1]["score_pct"] == 100.0


@pytest.mark.asyncio
async def test_lowest_rooms_as_inspector_forbidden(
    client: AsyncClient, db_session: AsyncSession,
):
    """Non-supervisor role gets 403."""
    user = await create_user(db_session, "insp", "pass", "inspector")
    headers = auth_header(user)
    resp = await client.get("/api/analytics/lowest-rooms", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_lowest_rooms_as_admin_allowed(
    client: AsyncClient, db_session: AsyncSession,
):
    """admin_ppi also has dashboard access per PRD."""
    user = await create_user(db_session, "admin", "pass", "admin_ppi")
    headers = auth_header(user)
    resp = await client.get("/api/analytics/lowest-rooms", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_lowest_rooms_empty(
    client: AsyncClient, db_session: AsyncSession,
):
    """No analytics data → empty array."""
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    headers = auth_header(supervisor)
    resp = await client.get("/api/analytics/lowest-rooms", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_lowest_rooms_filter_year_month(
    client: AsyncClient, db_session: AsyncSession,
):
    """Filter by YYYY-MM returns only that month's data."""
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "Ruang")
    item = await seed_item(db_session, "Item")

    # July: low score (0/4 = 0%)
    await _seed_approved_inspection(
        db_session, room.id, inspector.id, [item.id, item.id], [0, 0],
        business_date=date(2026, 7, 15),
    )
    # June: high score (4/4 = 100%)
    await _seed_approved_inspection(
        db_session, room.id, inspector.id, [item.id, item.id], [2, 2],
        business_date=date(2026, 6, 15),
    )

    headers = auth_header(supervisor)

    resp_jul = await client.get(
        "/api/analytics/lowest-rooms?year_month=2026-07&limit=5",
        headers=headers,
    )
    assert resp_jul.status_code == 200
    data = resp_jul.json()
    assert len(data) == 1
    assert data[0]["score_pct"] == 0.0

    resp_jun = await client.get(
        "/api/analytics/lowest-rooms?year_month=2026-06&limit=5",
        headers=headers,
    )
    assert resp_jun.status_code == 200
    data = resp_jun.json()
    assert len(data) == 1
    assert data[0]["score_pct"] == 100.0


@pytest.mark.asyncio
async def test_lowest_rooms_limit(
    client: AsyncClient, db_session: AsyncSession,
):
    """Respects limit parameter."""
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    item = await seed_item(db_session, "Item")
    rooms = [await seed_room(db_session, f"Ruang {i}") for i in range(5)]

    for room in rooms:
        await _seed_approved_inspection(
            db_session, room.id, inspector.id, [item.id], [1],
        )

    headers = auth_header(supervisor)
    resp = await client.get(
        "/api/analytics/lowest-rooms?limit=2", headers=headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_lowest_rooms_no_auth(client: AsyncClient):
    """No token → 401."""
    resp = await client.get("/api/analytics/lowest-rooms")
    assert resp.status_code == 401


# ── top-issues ──


@pytest.mark.asyncio
async def test_top_issues_ordered_by_frequency_desc(
    client: AsyncClient, db_session: AsyncSession,
):
    """Returns items sorted by score_zero_count descending."""
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "Ruang")
    i1 = await seed_item(db_session, "Item Sering")   # 0 in both → cnt=2
    i2 = await seed_item(db_session, "Item Kadang")    # 0 in first, 2 in second → cnt=1
    i3 = await seed_item(db_session, "Item Baik")      # 2 in both → cnt=0 (not in result)

    ids = [i1.id, i2.id, i3.id]
    await _seed_approved_inspection(
        db_session, room.id, inspector.id, ids, [0, 0, 2],
    )
    await _seed_approved_inspection(
        db_session, room.id, inspector.id, ids, [0, 2, 2],
    )

    headers = auth_header(supervisor)
    resp = await client.get("/api/analytics/top-issues?limit=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    # i1 has 2 zeros (highest), i2 has 1 zero
    assert len(data) == 2
    assert data[0]["item_id"] == i1.id
    assert data[0]["score_zero_count"] == 2
    assert data[1]["item_id"] == i2.id
    assert data[1]["score_zero_count"] == 1


@pytest.mark.asyncio
async def test_top_issues_empty(
    client: AsyncClient, db_session: AsyncSession,
):
    """No zero-score items → empty array."""
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "Ruang")
    item = await seed_item(db_session, "Item Baik")

    # All scores = 2 (no issues)
    await _seed_approved_inspection(
        db_session, room.id, inspector.id, [item.id, item.id, item.id], [2, 2, 2],
    )

    headers = auth_header(supervisor)
    resp = await client.get("/api/analytics/top-issues", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_top_issues_no_data(
    client: AsyncClient, db_session: AsyncSession,
):
    """No inspections at all → empty array."""
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    headers = auth_header(supervisor)
    resp = await client.get("/api/analytics/top-issues", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_top_issues_filter_year_month(
    client: AsyncClient, db_session: AsyncSession,
):
    """Filter by YYYY-MM returns only that month's data."""
    supervisor = await create_user(db_session, "sup", "pass", "supervisor")
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "Ruang")
    item = await seed_item(db_session, "Item")

    # July: one zero-score item
    await _seed_approved_inspection(
        db_session, room.id, inspector.id, [item.id], [0],
        business_date=date(2026, 7, 15),
    )
    # June: no zero-score items
    await _seed_approved_inspection(
        db_session, room.id, inspector.id, [item.id], [2],
        business_date=date(2026, 6, 15),
    )

    headers = auth_header(supervisor)

    resp_jul = await client.get(
        "/api/analytics/top-issues?year_month=2026-07", headers=headers,
    )
    assert resp_jul.status_code == 200
    assert len(resp_jul.json()) == 1

    resp_jun = await client.get(
        "/api/analytics/top-issues?year_month=2026-06", headers=headers,
    )
    assert resp_jun.status_code == 200
    assert resp_jun.json() == []


@pytest.mark.asyncio
async def test_top_issues_as_inspector_forbidden(
    client: AsyncClient, db_session: AsyncSession,
):
    """Non-supervisor role gets 403."""
    user = await create_user(db_session, "insp", "pass", "inspector")
    headers = auth_header(user)
    resp = await client.get("/api/analytics/top-issues", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_top_issues_no_auth(client: AsyncClient):
    """No token → 401."""
    resp = await client.get("/api/analytics/top-issues")
    assert resp.status_code == 401
