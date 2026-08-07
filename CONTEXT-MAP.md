# Context Map — RSUD Ajibarang Server Stack

This file maps the domain contexts in this repository. Each context has its own `CONTEXT.md` co-located with its module code under `backend/app/modules/<context>/` or at the frontend root `web-admin/`.

## Contexts

| Context | Path | Description |
|---------|------|-------------|
| 🔐 **auth** | `backend/app/modules/auth/CONTEXT.md` | User authentication, JWT tokens, sessions, roles & permissions |
| 📋 **inspection** | `backend/app/modules/inspection/CONTEXT.md` | Core inspection workflow: submit, approve, reject, scoring |
| 🏗️ **master** | `backend/app/modules/master/CONTEXT.md` | Master data: rooms, inspection items, soft-delete management |
| 📊 **analytics** | `backend/app/modules/analytics/CONTEXT.md` | CQRS analytics, dashboard stats, reporting |
| 🖼️ **media** | `backend/app/modules/media/CONTEXT.md` | Image upload, thumbnail generation, one-time token access |
| ⚙️ **background** | `backend/app/modules/background/CONTEXT.md` | Background jobs, outbox pattern, state machine |
| 🔧 **core** | `backend/app/core/CONTEXT.md` | Cross-cutting utilities: pagination, sorting, database, security, error responses, config |
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
- **Testing**: 68+ unit test (pytest-asyncio + in-memory SQLite), `PYTHONPATH=.` untuk `uv run`. Lihat ADR-0006.
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
| ADR-0008 | ✅ Accepted | User Management & Monitoring — User CRUD, Change Password, Inspector Performance |
| ADR-0009 | ✅ Accepted | Room-Item Many-to-Many Relationship — per-room inspection items via pivot table |
| ADR-0010 | ✅ Accepted | User-Room Assignment — inspector & supervisor assignment to rooms via pivot table |
| ADR-0011 | ✅ Accepted | Dashboard Dedicated Endpoint — satu endpoint untuk 4 card statistik dashboard |
| ADR-0012 | ✅ Accepted | Replace Photo Endpoint |
| ADR-0013 | ✅ Accepted | Room-Item Ordering — Urutan Item Inspeksi per Ruangan |

System-wide ADRs: `docs/adr/`

## Recent Updates

| Tanggal | Perubahan |
|---------|-----------|
| 7 Aug 2026 | ADR-0013: Room-Item Ordering — `sort_order` per ruangan di pivot `room_items` |
| 29 Jul 2026 | ADR-0011: Dashboard Dedicated Endpoint |
| 29 Jul 2026 | ADR-0009, ADR-0010, ADR-0011 added to ADR index |
| 29 Jul 2026 | Cross-cutting: User-Rooms bulk sync endpoint `GET /api/auth/user-rooms` |
| 29 Jul 2026 | Cross-cutting: per_page limit master data dinaikkan ke 10000 |
| 29 Jul 2026 | Web Admin: React Query DevTools, @tanstack/react-table, DataTable component |
