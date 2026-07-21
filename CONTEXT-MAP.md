# Context Map — RSUD Ajibarang Server Stack

This file maps the domain contexts in this repository. Each context has its own `CONTEXT.md` under `src/<context>/` with a glossary, key decisions, and bounded responsibilities.

## Contexts

| Context | Path | Description |
|---------|------|-------------|
| 🔐 **auth** | `src/auth/CONTEXT.md` | User authentication, JWT tokens, sessions, roles & permissions |
| 📋 **inspection** | `src/inspection/CONTEXT.md` | Core inspection workflow: submit, approve, reject, scoring |
| 🏗️ **master** | `src/master/CONTEXT.md` | Master data: rooms, inspection items, soft-delete management |
| 📊 **analytics** | `src/analytics/CONTEXT.md` | CQRS analytics, dashboard stats (weekly default), reporting |
| 🖼️ **media** | `src/media/CONTEXT.md` | Image upload, thumbnail generation, one-time token access |
| ⚙️ **background** | `src/background/CONTEXT.md` | Background jobs, outbox pattern, state machine |

## Cross-cutting concerns

- **Database conventions**: Fully normalized (header-detail), soft-delete (`is_active`), snapshot payloads, strict UTC (`DateTime(timezone=True)` via SQLAlchemy)
- **Auth**: JWT short-lived access + refresh tokens (httpOnly cookie), whitelist (`user_sessions`), admin revoke
- **Idempotency**: Composite unique constraint `(room_id, local_timestamp, inspector_id)`
- **Business Date**: Derived from `local_timestamp` (Android), not upload timestamp
- **Photos**: Multi-photo per item via `inspection_photos` table, local storage (Docker volume)
- **Scoring**: 0 (Berisiko+wajib foto), 1 (Minor Defect), 2 (Sesuai Standar)
- **System-wide ADRs**: `docs/adr/` — ADR-0001 (Frontend Stack), ADR-0002 (Multi-Photo Schema), ADR-0003 (JWT Auth)
