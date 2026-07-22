"""
Comprehensive seed data for end-to-end demo.

Usage: uv run python -m app.seed

Idempotent: skips users/rooms/items that already exist.
Inspection data is created fresh each run (for demo purposes).
"""

import asyncio
from datetime import date, datetime, timezone, timedelta

from sqlalchemy import select

from app.core.database import async_session
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.master.models import Room, InspectionItem
from app.modules.inspection.models import Inspection, InspectionDetail


async def seed():
    async with async_session() as db:
        # ── Users ──
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

        # ── Rooms ──
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
        room_objects = []
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

        # ── Inspection Items ──
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
        item_objects = []
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

        # ── Get reference objects ──
        users = {
            u.username: u for u in (
                await db.execute(select(User))
            ).scalars().all()
        }
        rooms = {
            r.name: r for r in (
                await db.execute(select(Room))
            ).scalars().all()
        }
        items = {
            i.name: i for i in (
                await db.execute(select(InspectionItem))
            ).scalars().all()
        }

        inspector = users["inspector"]
        supervisor = users["supervisor"]
        admin = users["admin"]

        now = datetime.now(timezone.utc)
        today = date.today()

        # ── Sample Inspection 1: APPROVED (UGD, 3 days ago) ──
        # Scores: mostly 2s and 1s, one 0, for analytics data
        insp1 = Inspection(
            room_id=rooms["UGD"].id,
            inspector_id=inspector.id,
            status="APPROVED",
            business_date=today - timedelta(days=3),
            local_timestamp=now - timedelta(days=3),
        )
        for idx, item in enumerate(item_objects):
            # Realistic scores: mostly 2s, some 1s, one 0
            score = 2
            if item.name == "Penggunaan APD":
                score = 1
            elif item.name == "Pengelolaan Limbah Medis":
                score = 1
            elif item.name == "Penandaan Area Risiko":
                score = 0  # Berisiko — needs photo

            insp1.details.append(InspectionDetail(
                item_id=item.id,
                item_name_snapshot=item.name,
                score=score,
            ))
        db.add(insp1)

        # ── Sample Inspection 2: APPROVED (Rawat Inap A, 2 days ago) ──
        insp2 = Inspection(
            room_id=rooms["Rawat Inap A"].id,
            inspector_id=inspector.id,
            status="APPROVED",
            business_date=today - timedelta(days=2),
            local_timestamp=now - timedelta(days=2),
        )
        for idx, item in enumerate(item_objects):
            score = 2
            if item.name == "Kebersihan Lingkungan":
                score = 0
            elif item.name == "Ketersediaan Sabun & Handuk":
                score = 0
            elif item.name == "Sterilisasi Alat":
                score = 1
            insp2.details.append(InspectionDetail(
                item_id=item.id,
                item_name_snapshot=item.name,
                score=score,
            ))
        db.add(insp2)

        # ── Sample Inspection 3: PENDING (ICU, today) ──
        insp3 = Inspection(
            room_id=rooms["ICU"].id,
            inspector_id=inspector.id,
            status="PENDING",
            business_date=today,
            local_timestamp=now,
        )
        for item in item_objects:
            insp3.details.append(InspectionDetail(
                item_id=item.id,
                item_name_snapshot=item.name,
                score=2,
            ))
        db.add(insp3)

        await db.commit()
        print(f"  ✅ 3 sample inspections created")

        # Populate analytics CQRS tables for the APPROVED inspections
        from app.modules.background.services import recalculate_analytics
        for insp in [insp1, insp2]:
            await recalculate_analytics(db, insp.id)
            print(f"  ✅ Analytics recalculated for inspection #{insp.id} (UGD/Rawat Inap A)")
        await db.commit()
        print()
        print("🎉 Seeding complete!")
        print()
        print("  Users:")
        print("    admin      / admin123      (admin_ppi)")
        print("    supervisor / supervisor123  (supervisor)")
        print("    inspector  / inspector123   (inspector)")
        print()
        print("  Rooms: UGD, Rawat Inap A, Rawat Inap B, ICU, Poliklinik, Kamar Operasi")
        print("  Items: 10 inspection items")
        print("  Inspections: 2 APPROVED (for analytics), 1 PENDING (for demo)")


if __name__ == "__main__":
    print("🌱 Seeding database...")
    asyncio.run(seed())
