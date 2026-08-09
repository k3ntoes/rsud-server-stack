"""
One-time cleanup: deactivate orphaned room_items.

A room_item is orphaned when:
  1. Its parent inspection_item is soft-deleted (is_active=False), OR
  2. Its parent room is soft-deleted (is_active=False)

These orphaned rows caused "Item #N" placeholder names in the web-admin
room checklist because the frontend couldn't find the item name.

Usage:
    cd backend
    DATABASE_URL=sqlite+aiosqlite:///./rsud.db uv run python -m scripts.cleanup_orphaned_room_items
    # or for PostgreSQL:
    DATABASE_URL=postgresql+asyncpg://rsud:rsud_secret@localhost:5433/rsud uv run python -m scripts.cleanup_orphaned_room_items

Dry-run by default. Pass --apply to actually update rows.
"""

import asyncio
import sys
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import async_session
from app.modules.master.models import Room, InspectionItem, RoomItem


async def cleanup(dry_run: bool = True):
    async with async_session() as db:
        # ── 1. Find orphaned room_items (parent item soft-deleted) ──
        result = await db.execute(
            select(RoomItem).where(RoomItem.is_active == True)
        )
        all_active_ri = list(result.scalars().all())

        orphans = []
        for ri in all_active_ri:
            item = await db.get(InspectionItem, ri.item_id)
            room = await db.get(Room, ri.room_id)
            if (item and not item.is_active) or (room and not room.is_active):
                orphans.append((ri, item, room))

        if not orphans:
            print("✅ No orphaned room_items found. Database is clean.")
            return

        print(f"\n🔍 Found {len(orphans)} orphaned room_item(s):\n")
        print(f"  {'room_item.id':<12} {'room':<20} {'item':<20} {'reason'}")
        print(f"  {'─'*12} {'─'*20} {'─'*20} {'─'*30}")
        for ri, item, room in orphans:
            room_name = room.name if room else f"(deleted id={ri.room_id})"
            item_name = item.name if item else f"(deleted id={ri.item_id})"
            reason = []
            if item and not item.is_active:
                reason.append("item inactive")
            if room and not room.is_active:
                reason.append("room inactive")
            print(f"  {ri.id:<12} {room_name:<20} {item_name:<20} {', '.join(reason)}")

        if dry_run:
            print(f"\n⚠️  Dry run — no changes made. Run with --apply to deactivate.")
        else:
            now = datetime.now(timezone.utc)
            for ri, _, _ in orphans:
                ri.is_active = False
                ri.updated_at = now
            await db.commit()
            print(f"\n✅ Deactivated {len(orphans)} orphaned room_item(s).")


def main():
    dry_run = "--apply" not in sys.argv
    asyncio.run(cleanup(dry_run=dry_run))


if __name__ == "__main__":
    main()
