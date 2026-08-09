"""
Comprehensive seed data for end-to-end demo.

Usage: uv run python -m app.seed

Idempotent: skips users/rooms/items that already exist.
Inspection data: uses composite unique key (room_id, local_timestamp, inspector_id)
to prevent duplicates on re-run.

╔══════════════════════════════════════════════════════════════╗
║  DATA COVERAGE (sesuai CONTEXT & ADR)                       ║
║                                                             ║
║  Users:     admin_ppi, supervisor, inspector                ║
║  Rooms:     6 ruangan (UGD, Rawat Inap A/B, ICU, dll)       ║
║  Items:     10 item inspeksi kebersihan                     ║
║  RoomItem:  All items → all rooms (ADR-0009)                 ║
║  UserRoom:  Inspector & supervisor → all rooms (ADR-0010)    ║
║                                                             ║
║  Inspections (total 12):                                     ║
║   ├─ Current month — 6 ruangan × 1-2 APPROVED = 12 inspeksi ║
║   ├─ Previous month — 2 ruangan × 1 APPROVED = 2 inspeksi   ║
║   ├─ REJECTED — 1 inspeksi (test rejection flow)              ║
║   └─ PENDING  — 1 inspeksi (test approval flow)              ║
║                                                             ║
║  Scores: varied (0=berisiko, 1=minor, 2=standar)             ║
║  → Analytics: lowest rooms, top issues populated             ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
from datetime import date, datetime, timezone, timedelta

from sqlalchemy import select

from app.core.database import async_session
from app.core.security import hash_password
from app.modules.auth.models import User, UserRoom
from app.modules.master.models import Room, InspectionItem, RoomItem
from app.modules.inspection.models import Inspection, InspectionDetail


# ── Item score patterns per room ──────────────────────────────────
# Each room has a tuple of (item_index, score) — index into item_names
# This creates realistic, varied score data for analytics.

ROOM_PROFILES: dict[str, list[tuple[int, int]]] = {
    # (item_index, score)  ← index 0 = "Kebersihan Tangan"
    "UGD": [
        (0, 2), (1, 1), (2, 2), (3, 0),   # limbah & lingkungan bermasalah
        (4, 2), (5, 2), (6, 1), (7, 2),
        (8, 2), (9, 2),
    ],
    "Rawat Inap A": [
        (0, 2), (1, 2), (2, 0), (3, 0),   # limbah & lingkungan berisiko
        (4, 1), (5, 2), (6, 2), (7, 2),
        (8, 0), (9, 2),                    # sabun habis
    ],
    "Rawat Inap B": [
        (0, 1), (1, 2), (2, 2), (3, 1),
        (4, 2), (5, 2), (6, 2), (7, 0),   # keamanan tempat tidur
        (8, 2), (9, 1),
    ],
    "ICU": [
        (0, 2), (1, 2), (2, 2), (3, 2),
        (4, 2), (5, 2), (6, 2), (7, 2),   # all perfect — best room
        (8, 2), (9, 2),
    ],
    "Poliklinik": [
        (0, 2), (1, 0), (2, 2), (3, 1),   # APD bermasalah
        (4, 1), (5, 2), (6, 2), (7, 2),
        (8, 2), (9, 0),                    # penandaan area risiko
    ],
    "Kamar Operasi": [
        (0, 2), (1, 2), (2, 2), (3, 2),
        (4, 1), (5, 0),                    # penyimpanan obat
        (6, 2), (7, 2), (8, 2), (9, 2),
    ],
}

# Profile for second-round inspections (UGD & Rawat Inap A)
ROOM_PROFILES_ROUND2: dict[str, list[tuple[int, int]]] = {
    "UGD": [
        (0, 2), (1, 2), (2, 1), (3, 2),   # improved from round 1
        (4, 2), (5, 2), (6, 2), (7, 2),
        (8, 2), (9, 2),
    ],
    "Rawat Inap A": [
        (0, 1), (1, 2), (2, 1), (3, 2),   # still some issues
        (4, 2), (5, 1), (6, 2), (7, 2),
        (8, 2), (9, 1),
    ],
}

# Profile for rejected inspection
ROOM_PROFILES_REJECTED: dict[str, list[tuple[int, int]]] = {
    "Rawat Inap B": [
        (0, 0), (1, 0), (2, 0), (3, 0),   # all zeros — totally failed
        (4, 0), (5, 0), (6, 0), (7, 0),
        (8, 0), (9, 0),
    ],
}

# June profiles — worse scores historically (before improvements)
ROOM_PROFILES_JUNE: dict[str, list[tuple[int, int]]] = {
    "UGD": [
        (0, 1), (1, 0), (2, 1), (3, 0),
        (4, 2), (5, 1), (6, 1), (7, 2),
        (8, 0), (9, 1),
    ],
    "ICU": [
        (0, 2), (1, 1), (2, 2), (3, 2),
        (4, 2), (5, 2), (6, 2), (7, 2),
        (8, 2), (9, 1),
    ],
}


async def seed():
    async with async_session() as db:
        # ──────────────── 1. USERS ────────────────
        users_data = [
            ("admin", "admin123", "admin_ppi"),
            ("supervisor", "supervisor123", "supervisor"),
            ("inspector", "inspector123", "inspector"),
        ]
        existing_users = {
            u.username for u in (
                await db.execute(select(User))
            ).scalars().all()
        }
        for username, password, role in users_data:
            if username in existing_users:
                print(f"  ⏭️  User '{username}' already exists")
                continue
            db.add(User(
                username=username,
                password_hash=hash_password(password),
                role=role,
            ))
            print(f"  ✅ User '{username}' ({role}) — password: {password}")
        await db.flush()

        # ──────────────── 2. ROOMS ────────────────
        room_names = [
            "UGD",
            "Rawat Inap A",
            "Rawat Inap B",
            "ICU",
            "Poliklinik",
            "Kamar Operasi",
        ]
        existing_rooms = {
            r.name for r in (
                await db.execute(select(Room))
            ).scalars().all()
        }
        room_objects: list[Room] = []
        for name in room_names:
            if name in existing_rooms:
                print(f"  ⏭️  Room '{name}' already exists")
                room = (await db.execute(
                    select(Room).where(Room.name == name)
                )).scalar_one()
                room_objects.append(room)
                continue
            room = Room(name=name)
            db.add(room)
            room_objects.append(room)
            print(f"  ✅ Room '{name}'")
        await db.flush()

        # ──────────────── 3. INSPECTION ITEMS ────────────────
        item_names = [
            "Kebersihan Tangan",
            "Penggunaan APD",
            "Pengelolaan Limbah Medis",
            "Kebersihan Lingkungan",
            "Sterilisasi Alat",
            "Penyimpanan Obat",
            "Identifikasi Pasien",
            "Keamanan Tempat Tidur",
            "Ketersediaan Sabun & Handuk",
            "Penandaan Area Risiko",
        ]
        existing_items = {
            i.name for i in (
                await db.execute(select(InspectionItem))
            ).scalars().all()
        }
        item_objects: list[InspectionItem] = []
        for name in item_names:
            if name in existing_items:
                item = (await db.execute(
                    select(InspectionItem).where(InspectionItem.name == name)
                )).scalar_one()
                item_objects.append(item)
                continue
            item = InspectionItem(name=name)
            db.add(item)
            item_objects.append(item)
        await db.flush()
        print(f"  ✅ {len(item_objects)} inspection items ready")

        # ──────────────── 4. ROOM-ITEM ASSIGNMENTS (ADR-0009) ────────────────
        for room in room_objects:
            for item in item_objects:
                existing = await db.execute(
                    select(RoomItem).where(
                        RoomItem.room_id == room.id,
                        RoomItem.item_id == item.id,
                    )
                )
                if existing.scalar_one_or_none() is None:
                    db.add(RoomItem(room_id=room.id, item_id=item.id))
        await db.commit()
        print(f"  ✅ Room-Item assignments ({len(room_objects)} rooms × {len(item_objects)} items)")

        # ──────────────── 5. USER-ROOM ASSIGNMENTS (ADR-0010) ────────────────
        users_all = (await db.execute(select(User))).scalars().all()
        for user in users_all:
            if user.role in ("inspector", "supervisor"):
                for room in room_objects:
                    existing = await db.execute(
                        select(UserRoom).where(
                            UserRoom.user_id == user.id,
                            UserRoom.room_id == room.id,
                        )
                    )
                    if existing.scalar_one_or_none() is None:
                        db.add(UserRoom(user_id=user.id, room_id=room.id))
        await db.commit()
        print(f"  ✅ User-Room assignments (inspector & supervisor → all rooms)")

        # ──────────────── 6. BUILD LOOKUPS ────────────────
        users_map = {
            u.username: u for u in (
                await db.execute(select(User))
            ).scalars().all()
        }
        rooms_map = {
            r.name: r for r in (
                await db.execute(select(Room))
            ).scalars().all()
        }

        inspector = users_map["inspector"]

        # ── Base datetime for idempotent re-runs ──
        # Anchored to "now" so demo data always lands in the current month
        # (dashboard/analytics default to the current month on the web).
        # Re-running later produces new timestamps → new inspection rows.
        SEED_EPOCH = datetime.now(timezone.utc)
        today = SEED_EPOCH.date()

        # ──────────────── 7. HELPER: CREATE INSPECTION ────────────────
        async def _make_inspection(
            room_name: str,
            days_ago: int,
            status: str,
            score_map: list[tuple[int, int]],
            inspector_id: int = inspector.id,
        ) -> Inspection | None:
            room = rooms_map[room_name]
            bdate = today - timedelta(days=days_ago)
            ts = SEED_EPOCH - timedelta(days=days_ago)

            # Check idempotency — skip if exact (room, ts, inspector) exists
            dup = await db.execute(
                select(Inspection).where(
                    Inspection.room_id == room.id,
                    Inspection.local_timestamp == ts,
                    Inspection.inspector_id == inspector_id,
                )
            )
            if dup.scalar_one_or_none() is not None:
                print(f"  ⏭️  Inspection '{room_name}' (D-{days_ago}) already exists")
                return None

            insp = Inspection(
                room_id=room.id,
                inspector_id=inspector_id,
                status=status,
                business_date=bdate,
                local_timestamp=ts,
            )
            for item_idx, score in score_map:
                item = item_objects[item_idx]
                insp.details.append(InspectionDetail(
                    item_id=item.id,
                    item_name_snapshot=item.name,
                    score=score,
                ))
            db.add(insp)
            await db.flush()
            return insp

        # ──────────────── 8. CREATE INSPECTIONS ────────────────

        created_inspections: list[Inspection] = []

        # ── 8a. Current month: 1 inspection per room ──
        print("\n  📋 Creating current-month inspections...")
        current_schedule = [
            ("UGD",          3,  ROOM_PROFILES["UGD"]),
            ("Rawat Inap A", 5,  ROOM_PROFILES["Rawat Inap A"]),
            ("Rawat Inap B", 4,  ROOM_PROFILES["Rawat Inap B"]),
            ("ICU",          2,  ROOM_PROFILES["ICU"]),
            ("Poliklinik",   6,  ROOM_PROFILES["Poliklinik"]),
            ("Kamar Operasi",7,  ROOM_PROFILES["Kamar Operasi"]),
        ]
        for room_name, days_ago, scores in current_schedule:
            insp = await _make_inspection(room_name, days_ago, "APPROVED", scores)
            if insp:
                created_inspections.append(insp)
                print(f"    ✅ {room_name} — APPROVED (D-{days_ago}, {len(scores)} items)")

        # ── 8b. Current-month round 2 — extra inspections for UGD & Rawat Inap A ──
        print("\n  📋 Creating current-month round 2 inspections (extra data)...")
        round2 = [
            ("UGD",          8,  ROOM_PROFILES_ROUND2["UGD"]),
            ("Rawat Inap A", 9,  ROOM_PROFILES_ROUND2["Rawat Inap A"]),
        ]
        for room_name, days_ago, scores in round2:
            insp = await _make_inspection(room_name, days_ago, "APPROVED", scores)
            if insp:
                created_inspections.append(insp)
                print(f"    ✅ {room_name} — APPROVED (D-{days_ago}, round 2)")

        # ── 8c. Previous month (for month filter testing) ──
        print("\n  📋 Creating previous-month inspections...")
        # ~30-35 days ago from the seed date lands in the previous month
        previous_schedule = [
            ("UGD",          32, ROOM_PROFILES_JUNE["UGD"]),
            ("ICU",          35, ROOM_PROFILES_JUNE["ICU"]),
        ]
        for room_name, days_ago, scores in previous_schedule:
            insp = await _make_inspection(room_name, days_ago, "APPROVED", scores)
            if insp:
                created_inspections.append(insp)
                print(f"    ✅ {room_name} — APPROVED (previous month)")

        # ── 8d. REJECTED inspection ──
        print("\n  📋 Creating REJECTED inspection...")
        rej = await _make_inspection(
            "Rawat Inap B", 1,
            "REJECTED",
            ROOM_PROFILES_REJECTED["Rawat Inap B"],
        )
        if rej:
            rej.rejection_reason = (
                "Semua item mendapat skor 0 (Berisiko). "
                "Perlu perbaikan menyeluruh dan inspeksi ulang."
            )
            created_inspections.append(rej)
            print(f"    ✅ Rawat Inap B — REJECTED (D-1, all zeros)")

        # ── 8e. PENDING inspection — for approval workflow ──
        print("\n  📋 Creating PENDING inspection (for approval test)...")
        pending = await _make_inspection(
            "ICU", 0,
            "PENDING",
            ROOM_PROFILES["ICU"],
        )
        if pending:
            created_inspections.append(pending)
            print(f"    ✅ ICU — PENDING (today, ready for approval)")

        await db.commit()
        print(f"\n  ✅ Total inspections created: {len(created_inspections)}")

        # ──────────────── 9. RECALCULATE ANALYTICS ────────────────
        # Only for APPROVED inspections (REJECTED & PENDING don't count)
        print("\n  ⚙️  Recalculating analytics for APPROVED inspections...")
        from app.modules.background.services import recalculate_analytics
        approved = [i for i in created_inspections if i.status == "APPROVED"]
        for insp in approved:
            await recalculate_analytics(db, insp.id)
            print(f"    ✅ Analytics done — inspection #{insp.id} ({insp.business_date})")
        print(f"  ✅ Analytics recalculated for {len(approved)} APPROVED inspections")

        await db.commit()

        # ──────────────── 10. SUMMARY ────────────────
        print()
        print("╔═══════════════════════════════════════════════════════╗")
        print("║             🌱  SEEDING COMPLETE!                    ║")
        print("╠═══════════════════════════════════════════════════════╣")
        print("║                                                     ║")
        print("║  Users:                                              ║")
        print("║    admin      / admin123      (admin_ppi)            ║")
        print("║    supervisor / supervisor123  (supervisor)          ║")
        print("║    inspector  / inspector123   (inspector)           ║")
        print("║                                                     ║")
        print("║  Rooms: 6 (UGD, Rawat Inap A/B, ICU, dll)           ║")
        print("║  Items: 10 inspection items                          ║")
        print("║                                                     ║")
        print(f"║  Inspections: {len(created_inspections)} total                          ║")
        print(f"║    ├─ Current month APPROVED:   {len([i for i in created_inspections if i.status == 'APPROVED' and (today - i.business_date).days <= 31])}  ║")
        print(f"║    ├─ Previous month APPROVED:  {len([i for i in created_inspections if i.status == 'APPROVED' and (today - i.business_date).days > 31])}  ║")
        print(f"║    ├─ REJECTED:       {len([i for i in created_inspections if i.status == 'REJECTED'])}  ║")
        print(f"║    └─ PENDING:        {len([i for i in created_inspections if i.status == 'PENDING'])}  ║")
        print("║                                                     ║")
        print("║  📊 Analytics page shows:                           ║")
        print("║    • 6 rooms with score data                        ║")
        print("║    • Multiple issue items (score=0)                 ║")
        print("║    • Previous month data                            ║")
        print("║    • Inspector performance                          ║")
        print("║                                                     ║")
        print("╚═══════════════════════════════════════════════════════╝")
        print()


if __name__ == "__main__":
    print("🌱 Seeding database...")
    print()
    asyncio.run(seed())
