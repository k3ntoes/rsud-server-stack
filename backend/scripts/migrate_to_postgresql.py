"""
SQLite → PostgreSQL data migration script.

Usage:
    # Ensure PostgreSQL is running (make db-up)
    # Then run:
    DATABASE_URL_SRC=sqlite+aiosqlite:///./rsud.db \
    DATABASE_URL_DST=postgresql+asyncpg://rsud:rsud_secret@localhost:5433/rsud \
    uv run python -m scripts.migrate_to_postgresql

What it does:
    1. Reads all tables from SQLite via SQLAlchemy ORM
    2. Saves data as dicts (handles type coercions)
    3. Writes to PostgreSQL, preserving FK relationships
    4. Resets PostgreSQL sequences for auto-increment IDs
"""

import asyncio
import os
import sys
from datetime import date, datetime

from sqlalchemy import Date, DateTime, select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# ── Import all ORM models so metadata is populated ──
from app.core.database import Base
from app.modules.auth.models import User, UserSession, UserRoom
from app.modules.master.models import Room, InspectionItem, RoomItem
from app.modules.inspection.models import Inspection, InspectionDetail, InspectionPhoto
from app.modules.analytics.models import RoomMonthlyStats, IssueFrequencyStats
from app.modules.background.models import BackgroundJob

# ── Ordered tables for data extraction (respect FK dependencies) ──
TABLES_IN_ORDER = [
    User,           # parent — no FK
    Room,           # parent — no FK
    InspectionItem, # parent — no FK
    UserRoom,       # child  — FK to User, Room
    RoomItem,       # child  — FK to Room, InspectionItem
    Inspection,     # child  — FK to Room, User
    InspectionDetail, # child — FK to Inspection, InspectionItem
    InspectionPhoto,  # child — FK to InspectionDetail
    UserSession,     # child — FK to User
    RoomMonthlyStats, # parent — no FK
    IssueFrequencyStats, # parent — no FK
    BackgroundJob,   # parent — no FK
]


def _serialize_value(val):
    """Convert Python/DB types to JSON-safe values for cross-DB transfer."""
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, bool):
        return bool(val)
    # Decimal, UUID, etc.
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return val


async def _extract_all(db: AsyncSession) -> dict:
    """Extract all data from SQLite source as dicts."""
    data = {}
    for model in TABLES_IN_ORDER:
        table_name = model.__tablename__
        result = await db.execute(select(model))
        rows = result.scalars().all()
        serialized = []
        for row in rows:
            record = {}
            for col in model.__table__.columns:
                val = getattr(row, col.name)
                record[col.name] = _serialize_value(val)
            serialized.append(record)
        data[table_name] = serialized
        print(f"  📦 {table_name}: {len(serialized)} rows")
    return data


async def _import_all(db: AsyncSession, data: dict) -> None:
    """Import all data into PostgreSQL, preserving FK relationships."""
    for model in TABLES_IN_ORDER:
        table_name = model.__tablename__
        rows = data.get(table_name, [])
        if not rows:
            print(f"  ⏭️  {table_name}: no data to import")
            continue

        for row_data in rows:
            # Parse ISO timestamps back to datetime objects
            for col_name, val in row_data.items():
                col = model.__table__.columns.get(col_name)
                if col is None:
                    continue
                if isinstance(val, str) and val and isinstance(col.type, type):
                    type_cls = type(col.type)
                    if issubclass(type_cls, (DateTime, Date)):
                        try:
                            parsed = datetime.fromisoformat(val)
                            if issubclass(type_cls, Date) and not issubclass(type_cls, DateTime):
                                row_data[col_name] = parsed.date()
                            else:
                                row_data[col_name] = parsed
                        except (ValueError, TypeError):
                            pass  # keep as string

            # Create model instance
            instance = model(**row_data)
            db.add(instance)

        await db.commit()
        print(f"  ✅ {table_name}: {len(rows)} rows imported")

    # Reset sequences for auto-increment columns
    print("  🔄 Resetting sequences...")
    for model in TABLES_IN_ORDER:
        table_name = model.__tablename__
        pk_col = model.__table__.primary_key.columns.keys()[0]
        max_id = max((r.get(pk_col, 0) or 0) for r in data.get(table_name, []))
        if max_id > 0:
            seq_name = f"{table_name}_{pk_col}_seq"
            try:
                # PostgreSQL uses sequences for SERIAL/IDENTITY columns
                await db.execute(
                    text(f"SELECT setval('{seq_name}', {max_id}, true)")
                )
            except Exception:
                # Some tables won't have sequences — that's fine
                pass

    await db.commit()
    print("  ✅ Sequences reset")


async def migrate():
    src_url = os.environ.get("DATABASE_URL_SRC")
    dst_url = os.environ.get("DATABASE_URL_DST")

    if not src_url or not dst_url:
        print("❌ Please set DATABASE_URL_SRC and DATABASE_URL_DST")
        print("   Example:")
        print("   DATABASE_URL_SRC=sqlite+aiosqlite:///./rsud.db")
        print("   DATABASE_URL_DST=postgresql+asyncpg://rsud:rsud_secret@localhost:5433/rsud")
        sys.exit(1)

    print("🔍 Connecting to SQLite (source)...")
    src_engine = create_async_engine(src_url)
    src_session = async_sessionmaker(src_engine, class_=AsyncSession)

    print("🔍 Connecting to PostgreSQL (destination)...")
    dst_engine = create_async_engine(dst_url)
    dst_session = async_sessionmaker(dst_engine, class_=AsyncSession)

    # ── Step 1: Extract all from SQLite ──
    print("\n📤 Step 1: Extracting data from SQLite...")
    async with src_session() as db:
        data = await _extract_all(db)

    # ── Step 2: Run migrations on PostgreSQL (create tables) ──
    print("\n🏗️  Step 2: Creating PostgreSQL schema...")
    async with dst_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ── Step 3: Import all into PostgreSQL ──
    print("\n📥 Step 3: Importing data into PostgreSQL...")
    async with dst_session() as db:
        await _import_all(db, data)

    # ── Cleanup ──
    await src_engine.dispose()
    await dst_engine.dispose()

    print("\n🎉 Migration complete!")
    print(f"   Source: {src_url}")
    print(f"   Destination: {dst_url}")
    print("\n   Next steps:")
    print("   1. Start backend with PostgreSQL: make dev-pg")
    print("   2. Or run full stack: docker compose up --build -d")


if __name__ == "__main__":
    asyncio.run(migrate())
