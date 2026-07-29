# Context: Core — Cross-Cutting Utilities

## Responsibility

Provide shared infrastructure and utilities used by all modules: database engine setup, security primitives (JWT + password hashing), pagination helpers, sorting with SQL injection protection, standardized error responses, and reusable FastAPI dependencies.

## Location

`backend/app/core/` — bukan module domain, melainkan shared infrastructure yang tidak memiliki tanggung jawab bisnis spesifik.

## Files

| File | Tanggung Jawab |
|------|----------------|
| `config.py` | Application settings via `pydantic-settings` (env vars / `.env` file) |
| `database.py` | SQLAlchemy async engine, session factory, `Base` ORM class, SQLite FK pragma |
| `security.py` | JWT access/refresh token creation + verification, bcrypt password hashing |
| `dependencies.py` | FastAPI `Depends(get_current_user)` — JWT bearer auth → User model |
| `pagination.py` | `PaginatedResponse[T]` model + `paginate()` helper |
| `sorting.py` | `apply_sorting()` — allowlist-based ORDER BY (anti SQL injection) |
| `errors.py` | `error_response()` — standardized `{ detail, code }` JSON response |

## Language

| Term | Definition |
|------|------------|
| PaginatedResponse | Pydantic generic model `{ items, total, page, per_page, total_pages }` — digunakan oleh semua endpoint LIST |
| paginate() | Helper function: `paginate(items, total, page, per_page) → PaginatedResponse` — menghitung `total_pages = ceil(total / per_page)` |
| SyncResponse | (Defined in `master/schemas.py`) — wrapper `{ data, synced_at }` untuk Android sync mode, bukan bagian dari core |
| Sorting Allowlist | `_SORTABLE` dict — mapping model → set kolom yang diizinkan untuk sorting. Mencegah SQL injection via arbitrary column names |
| apply_sorting() | `apply_sorting(query, model, sort_by, sort_order) → Select` — tambah ORDER BY jika `sort_by` ada di allowlist |
| get_current_user | FastAPI dependency — verify JWT access token, fetch user from DB, raise 401 jika invalid |
| error_response() | `error_response(status_code, detail, code) → JSONResponse` — return `{ "detail": "...", "code": "..." }` |
| JWT | JSON Web Token — short-lived access token (15 menit) + long-lived refresh token (7 hari) |
| bcrypt | Password hashing algorithm — digunakan via `hash_password()` / `verify_password()` |
| SQLite FK Pragma | `PRAGMA foreign_keys=ON` — diaktifkan per-connection karena SQLite nonaktifkan FK constraint secara default |

## Key Decisions

### Pagination

- **Server-driven**: Backend menentukan `page`/`per_page`, frontend hanya mengirim parameter. Tidak ada client-driven pagination (offset/limit manual).
- **Generic model**: `PaginatedResponse[T]` menggunakan `Generic[T]` — reusable untuk semua model tanpa duplikasi schema.
- **Minimum 1 halaman**: `total_pages = max(1, ceil(total / per_page))` — tidak ada `total_pages = 0` meskipun data kosong.
- **per_page limit berbeda per module**: Master data `le=10000` (karena Android sync butuh all-data), auth/inspection `le=100` (resource lebih sensitif).

### Sorting

- **Allowlist-based**: Sorting hanya diizinkan untuk kolom yang terdaftar di `_SORTABLE` dict. Kolom arbitrary (termasuk relasi/expression) tidak bisa di-sort.
- **Silent fallback**: Jika `sort_by` tidak ada di allowlist, query tetap jalan tanpa ORDER BY — tidak raise error.
- **Model-specific**: Setiap model punya allowlist sendiri — `User` bisa sort `username`, `Room` bisa sort `name`, dll.

### Database

- **Dual database**: SQLite + aiosqlite (development), PostgreSQL + asyncpg (production). Dikontrol via `DATABASE_URL` env var.
- **SQLite FK**: `PRAGMA foreign_keys=ON` di-enable via SQLAlchemy event listener — penting karena SQLite nonaktifkan FK constraint secara default.
- **expire_on_commit=False**: Mencegah detach object setelah commit — memungkinkan akses ke relasi yang di-loaded secara eager.
- **Base class**: `DeclarativeBase` dari SQLAlchemy 2.0 — semua model inherit dari sini.

### Security

- **JWT dual-token**: Access Token (15 menit, `type: "access"`), Refresh Token (7 hari, `type: "refresh"`). Keduanya diverifikasi dengan `jose.jwt.decode()`, ditingkatkan dengan `exp` claim.
- **bcrypt langsung**: Tidak melalui passlib — langsung menggunakan `bcrypt.hashpw()` / `bcrypt.checkpw()` untuk menghindari dependency passlib dan kompatibilitas bcrypt. (Passlib sebelumnya digunakan tapi diganti karena bcrypt>=4.1 mengubah internal `__about__` module.)
- **JWT_SECRET fallback**: Default `"change-me-in-production"` — wajib diubah di environment production.

### Dependencies

- **get_current_user**: Satu dependency utama untuk semua protected endpoint. Memverifikasi JWT, memeriksa token type (`access`), fetch user dari DB, cek `is_active`.
- **HTTPBearer**: FastAPI `HTTPBearer` scheme — otomatis parse `Authorization: Bearer` header.
- **401 vs 403**: FastAPI HTTPBearer return 401 jika token missing/invalid. 403 digunakan untuk role-based authorization di module-level.

### Error Response

- **Standardized format**: Semua error return `{ "detail": "human readable", "code": "MACHINE_CODE" }`.
- **Android Interceptor**: Field `code` digunakan oleh Android Interceptor untuk deteksi error type yang reliable — lebih stabil daripada parsing `detail` string.
- **ErrorResponse class**: Satu fungsi `error_response()` — reusable di semua module.

## Dependencies

| Dependency | Versi (uv.lock) | Kegunaan |
|------------|-----------------|----------|
| `fastapi` | ^0.115 | Web framework |
| `uvicorn` | ^0.34 | ASGI server |
| `sqlalchemy` | ^2.0 | ORM + async engine |
| `aiosqlite` | ^0.20 | SQLite async driver (dev) |
| `asyncpg` | ^0.30 | PostgreSQL async driver (prod) |
| `python-jose[cryptography]` | — | JWT encode/decode |
| `bcrypt` | <4.1 | Password hashing |
| `pydantic-settings` | — | Settings management via env vars |
| `pydantic` | ^2.0 | Data validation, BaseModel |

## Cross-module Usage

| Core File | Digunakan Oleh |
|-----------|----------------|
| `database.py` | Semua module (via `get_db` dependency) |
| `dependencies.py` | Semua protected endpoint (via `Depends(get_current_user)`) |
| `security.py` | `auth/` module (login, refresh, change-password) |
| `pagination.py` | `auth/api.py`, `master/api.py`, `inspection/api.py` |
| `sorting.py` | `auth/services.py`, `master/services.py`, `inspection/services.py` |
| `errors.py` | `auth/api.py`, `master/api.py`, `inspection/api.py`, `media/api.py` |
| `config.py` | Semua module (via `from app.config import settings`) |

## ADRs

| ADR | Judul | Relevansi |
|-----|-------|-----------|
| ADR-0003 | JWT Layered Auth dengan httpOnly Refresh Cookie | Security (dual token) |
| ADR-0004 | SQLite + aiosqlite Dev, PostgreSQL Prod | Database setup |
| ADR-0005 | Async ORM Strategy — `joinedload` over `selectinload` | Database (eager loading) |
| ADR-0006 | Test Strategy — pytest-asyncio + In-Memory SQLite | Database (test setup) |
| ADR-0011 | Dashboard Dedicated Endpoint | Pagination (per_page limit extension) |

See `docs/adr/` for details.
