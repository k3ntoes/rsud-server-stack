# Architecture — RSUD Ajibarang Server Stack

## Tech Stack

| Layer | Teknologi | Catatan |
|-------|-----------|---------|
| **Backend** | FastAPI (Python) | Async-first, Pydantic validation |
| **Package Manager** | `uv` (Astral) | Fast, pip-compatible, menggantikan pip/poetry |
| **ORM** | SQLAlchemy 2.0 | `Mapped` + `mapped_column`, async session |
| **Database** | SQLite (dev) / PostgreSQL (prod) | SQLite via aiosqlite untuk dev cepat, PostgreSQL via asyncpg untuk produksi |
| **Migration** | Alembic | Auto-generate dari SQLAlchemy models |
| **Auth** | JWT (Access + Refresh) | httpOnly cookie, whitelist `user_sessions` |
| **Frontend** | React + Vite | TanStack Router + TanStack Query + shadcn/ui |
| **Container** | Docker + docker-compose | Multi-stage build, reverse proxy (TBD) |

---

## 1. Package Manager: `uv`

`uv` digunakan sebagai package manager untuk backend Python. Menggantikan `pip`, `poetry`, dan `venv`.

### Perintah Dasar

```bash
# Install uv (jika belum ada)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Init project
uv init --app

# Add dependencies
uv add fastapi "fastapi[standard]" sqlalchemy aiosqlite alembic python-jose passlib[bcrypt] python-multipart

# Dev vs Prod:
#   Dev:  sqlite+aiosqlite:///./rsud.db (zero setup, file-based)
#   Prod: postgresql+asyncpg://user:pass@db:5432/rsud

# Add dev dependencies
uv add --dev pytest pytest-asyncio

# Run project
uv run fastapi dev app/main.py

# Sync environment
uv sync
```

### File yang Digunakan

- **`pyproject.toml`** — deklarasi dependencies (menggantikan `requirements.txt`)
- **`uv.lock`** — lockfile untuk reproducible builds (auto-generated)
- **`.python-version`** — versi Python yang digunakan

### Docker Multi-Stage Build

```dockerfile
# Stage 1: Install dependencies with uv
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
```

---

## 2. Backend Structure

```
backend/
├── app/
│   ├── main.py                     # Entry point FastAPI
│   ├── config.py                   # Settings (pydantic-settings)
│   │
│   ├── core/                       # Shared infrastructure
│   │   ├── database.py             # AsyncSession, engine
│   │   ├── security.py             # JWT, password hashing
│   │   └── dependencies.py         # Global dependencies (get_db, get_current_user)
│   │
│   ├── modules/                    # Domain modules
│   │   ├── auth/                   # 🔐 Autentikasi & otorisasi
│   │   │   ├── api.py              #   Routes: login, refresh, logout, me
│   │   │   ├── models.py           #   SQLAlchemy: User, UserSession
│   │   │   ├── schemas.py          #   Pydantic: LoginRequest, TokenResponse
│   │   │   ├── services.py         #   Business logic: authenticate, create_user
│   │   │   └── dependencies.py     #   Per-module dependencies: get_admin_user
│   │   │
│   │   ├── master/                 # 🏗️ Master data
│   │   │   ├── api.py
│   │   │   ├── models.py           #   Room, InspectionItem
│   │   │   ├── schemas.py
│   │   │   └── services.py
│   │   │
│   │   ├── inspection/             # 📋 Inspeksi
│   │   │   ├── api.py
│   │   │   ├── models.py           #   Inspection, InspectionDetail, InspectionPhoto
│   │   │   ├── schemas.py
│   │   │   └── services.py
│   │   │
│   │   ├── media/                  # 🖼️ Upload & thumbnail
│   │   │   ├── api.py
│   │   │   └── services.py
│   │   │
│   │   ├── analytics/              # 📊 Dashboard (read-only)
│   │   │   ├── api.py
│   │   │   ├── models.py           #   RoomMonthlyStats, IssueFrequencyStats
│   │   │   └── services.py
│   │   │
│   │   └── background/             # ⚙️ Background jobs
│   │       ├── models.py           #   BackgroundJob
│   │       ├── services.py         #   Outbox pattern processor
│   │       └── worker.py           #   Async worker loop
│   │
│   └── alembic/                    # Database migrations
│       ├── env.py
│       └── versions/
│
├── uploads/                        # Foto di-mount sebagai Docker volume
│
├── pyproject.toml                  # Dependencies (managed by uv)
├── uv.lock                         # Lockfile
├── .python-version                 # Versi Python
└── Dockerfile
```

### Arsitektur per Module (3 Layer)

```
API Layer (api.py)          → HTTP concerns, validasi input
    ↓ call
Service Layer (services.py) → Business logic, koordinasi data
    ↓ call
Data Layer (models.py)      → SQLAlchemy ORM, query ke database
```

**Aturan per Layer:**
- **API Layer** — thin. Unpack request, panggil service, return schema. Tidak ada business logic.
- **Service Layer** — business rules. Tidak tahu soal HTTP/FastAPI dependencies.
- **Data Layer** — SQLAlchemy models + queries. Tidak ada validasi bisnis.

---

## 3. Database Patterns

### SQLAlchemy 2.0

```python
# models.py
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))  # admin_ppi | supervisor | inspector
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

### Soft-Delete Convention
- Semua tabel transaksional punya kolom `is_active` (Boolean, default True).
- Query wajib filter `WHERE is_active = True`.
- Hard-delete dilarang.

### Naming Convention
- Tabel: `snake_case` plural (`users`, `inspection_details`, `inspection_photos`)
- Kolom: `snake_case` (`created_at`, `is_active`, `item_name_snapshot`)
- Primary Key: `id`
- Foreign Key: `<table>_id` (`room_id`, `inspector_id`)

---

## 4. Deployment Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│              │     │              │     │              │
│   Android    │────▶│   FastAPI    │────▶│  SQLite/     │
│              │     │              │     │  PostgreSQL  │
│   (Client)   │     │   (Backend)  │     │  (Database)  │
│              │     │              │     │              │
└──────────────┘     │  :8000/api   │     └──────────────┘
                     │              │
┌──────────────┐     │  :8000/docs  │
│              │     │              │     ┌──────────────┐
│   Browser    │────▶│  Background  │────▶│   Uploads/   │
│   (React)    │     │   Worker     │     │  (Volume)    │
│              │     │              │     └──────────────┘
└──────────────┘     └──────────────┘
```

- **Reverse Proxy** (Traefik/Caddy) di depan FastAPI — handle HTTPS, routing
- **React SPA** di-serve via Nginx sebagai static files
- **Semua container** dalam 1 docker-compose network
- Frontend call API via reverse proxy (no CORS issues)

### Environment Variables

Semua konfigurasi rahasia via environment variables — tidak ada hardcoded secrets di kode.

```
# backend/.env.example (jangan commit .env asli)
# Dev:   DATABASE_URL=sqlite+aiosqlite:///./rsud.db
# Prod:  DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/rsud
DATABASE_URL=sqlite+aiosqlite:///./rsud.db
JWT_SECRET=<random-256bit-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
UPLOAD_DIR=/app/uploads
```

- **Development**: via `.env` file + docker-compose
- **Production**: via docker-compose `environment:` atau platform secrets
- **Wajib** ada di semua environment: `DATABASE_URL`, `JWT_SECRET`

### .dockerignore

```
# .dockerignore (root — berlaku untuk semua Docker build di monorepo)
.venv/
.git/
.gitignore
.gitnexusignore
.env
*.md
tests/
node_modules/
```

Mencegah Docker build meng-copy environment lokal dan file tidak perlu, mempercepat build.

---

## 5. Key Architecture Decisions (ADRs)

| ADR | Judul |
|-----|-------|
| 0001 | React + Vite + TanStack sebagai Frontend Stack |
| 0002 | Multi-Photo Schema — Tabel `inspection_photos` Terpisah |
| 0003 | JWT Layered Auth dengan httpOnly Refresh Cookie |

Lihat `docs/adr/` untuk detail setiap keputusan.

---

## 6. Diagram Alur Data

### Auth Flow
```
Login Request → POST /api/auth/login
  → Validasi username + password (passlib[bcrypt])
  → Generate Access Token (15m) + Refresh Token (7d)
  → Simpan Refresh Token di user_sessions (whitelist)
  → Set Refresh Token sebagai httpOnly cookie
  → Return { access_token, user } ke client

Setiap Request → Authorization: Bearer <access_token>
  → Validasi JWT signature
  → Cek expiry
  → Inject user ke request (dependency)
```

### Inspection Submission Flow
```
Android → POST /api/upload (file foto) → return photo_file_name
Android → POST /api/inspections (JSON + photo_file_names)
  → Validasi idempotency (room_id, local_timestamp, inspector_id)
  → Validasi semua item wajib di-cek
  → Buat inspection + details + photos
  → Status: PENDING

Supervisor → GET /api/inspections?status=PENDING
  → Lihat thumbnail foto (lazy load)
Supervisor → POST /api/inspections/{id}/approve
  atau POST /api/inspections/{id}/reject + reason
  
  → Jika APPROVED → Trigger background job:
    1. Hitung skor → UPSERT room_monthly_stats
    2. Hitung frekuensi skor 0 → UPSERT issue_frequency_stats
```

### Background Jobs (Outbox Pattern)
```
Inspeksi APPROVED → INSERT ke background_jobs (task_type, reference_id, status=PENDING)
Worker loop → SELECT * FROM background_jobs WHERE status=PENDING
  → Process task
  → UPDATE status = COMPLETED atau FAILED
  → Jika FAILED → retry (self-healing)
```
