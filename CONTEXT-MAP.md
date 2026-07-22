# Context Map — RSUD Ajibarang Server Stack

This file maps the domain contexts in this repository. Each context has its own `CONTEXT.md` co-located with its module code under `backend/app/modules/<context>/` or at the frontend root `web-admin/`.

## Contexts

| Context | Path | Description |
|---------|------|-------------|
| 🔐 **auth** | `backend/app/modules/auth/CONTEXT.md` | User authentication, JWT tokens, sessions, roles & permissions |
| 📋 **inspection** | `backend/app/modules/inspection/CONTEXT.md` | Core inspection workflow: submit, approve, reject, scoring |
| 🏗️ **master** | `backend/app/modules/master/CONTEXT.md` | Master data: rooms, inspection items, soft-delete management |
| 📊 **analytics** | `backend/app/modules/analytics/CONTEXT.md` | CQRS analytics, dashboard stats (weekly default), reporting |
| 🖼️ **media** | `backend/app/modules/media/CONTEXT.md` | Image upload, thumbnail generation, one-time token access |
| ⚙️ **background** | `backend/app/modules/background/CONTEXT.md` | Background jobs, outbox pattern, state machine |
| 🖥️ **web-admin** | `web-admin/CONTEXT.md` | Frontend SPA: auth patterns, hooks, routing, Planograph UI |

## Cross-cutting concerns

- **Database**: SQLite + aiosqlite (development), PostgreSQL + asyncpg (production). Dikontrol via `DATABASE_URL` env var. Lihat ADR-0004.
- **Auth**: JWT short-lived access + refresh tokens (httpOnly cookie), whitelist (`user_sessions`), admin revoke. `bcrypt<4.1` pin untuk kompatibilitas passlib. Lihat ADR-0003, ADR-0007.
- **ORM Strategy**: Wajib `joinedload` untuk eager loading di async context — `selectinload` menyebabkan `MissingGreenlet` error bersama aiosqlite. Lihat ADR-0005.
- **Database conventions**: Fully normalized (header-detail), soft-delete (`is_active`), snapshot payloads, strict UTC (`DateTime(timezone=True)` via SQLAlchemy)
- **Idempotency**: Composite unique constraint `(room_id, local_timestamp, inspector_id)`
- **Business Date**: Derived from `local_timestamp` (Android), not upload timestamp
- **Photos**: Multi-photo per item via `inspection_photos` table, local storage (Docker volume)
- **Scoring**: 0 (Berisiko+wajib foto), 1 (Minor Defect), 2 (Sesuai Standar)
- **Dev Port**: Backend di port 8100 (8000 digunakan oleh Portainer di host). Sesuaikan di `.env` jika perlu.
- **Testing**: 35 unit test (pytest-asyncio + in-memory SQLite), `PYTHONPATH=.` untuk `uv run`. Lihat ADR-0006.
- **Tooling**: `PYTHONPATH=.` diperlukan untuk semua command `uv run` (uv tidak menambahkan cwd ke Python path secara default)

## ADR Index

| ADR | Status | Topik |
|-----|--------|-------|
| ADR-0001 | ✅ Accepted | React + Vite + TanStack sebagai Frontend Stack |
| ADR-0002 | ✅ Accepted | Multi-Photo Schema — Tabel `inspection_photos` Terpisah |
| ADR-0003 | ✅ Accepted | JWT Layered Auth dengan httpOnly Refresh Cookie |
| ADR-0004 | ✅ Accepted | SQLite + aiosqlite Dev, PostgreSQL Prod |
| ADR-0005 | ✅ Accepted | Async ORM Strategy — `joinedload` over `selectinload` |
| ADR-0006 | ✅ Accepted | Test Strategy — pytest-asyncio + In-Memory SQLite |
| ADR-0007 | ✅ Accepted | Frontend Auth Pattern — SessionStorage + Auto-Refresh Token |

System-wide ADRs: `docs/adr/`
