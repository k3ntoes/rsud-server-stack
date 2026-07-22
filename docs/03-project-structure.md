# Project Structure — RSUD Ajibarang Server Stack

## Monorepo Layout

```
rsud-server-stack/
│
├── .github/workflows/              # CI/CD pipelines (Test & Deploy)
│
├── .dockerignore                   # Docker ignore rules
├── .gitignore                      # Git ignore rules
├── .gitnexusignore                 # GitNexus indexing ignore rules
├── README.md                       # Project overview & getting started
├── docker-compose.yml              # Orkestrasi utama (API, DB, Web, Reverse Proxy)
├── CODING-RULES.md                 # Coding best practices untuk AI agent
│
├── backend/                        # FastAPI Backend (Python)
│   ├── app/
│   │   ├── main.py                 # Entry point FastAPI
│   │   ├── config.py               # Settings via pydantic-settings
│   │   ├── core/                   # Shared infrastructure
│   │   │   ├── database.py         #   AsyncSession, engine
│   │   │   ├── security.py         #   JWT, password hashing
│   │   │   └── dependencies.py     #   Global deps (get_db, get_current_user)
│   │   ├── modules/                # Domain modules (modular architecture)
│   │   │   ├── auth/               #   🔐 Autentikasi & otorisasi
│   │   │   │   ├── api.py          #     Routes
│   │   │   │   ├── models.py       #     SQLAlchemy models
│   │   │   │   ├── schemas.py      #     Pydantic schemas
│   │   │   │   ├── services.py     #     Business logic
│   │   │   │   └── dependencies.py #     Per-module dependencies
│   │   │   ├── master/             #   🏗️ Master data
│   │   │   ├── inspection/         #   📋 Inspeksi
│   │   │   ├── media/              #   🖼️ Upload & thumbnail
│   │   │   ├── analytics/          #   📊 Dashboard (read-only)
│   │   │   └── background/         #   ⚙️ Background jobs
│   │   └── alembic/                # Database migrations
│   ├── uploads/                    # Foto (Docker volume)
│   ├── pyproject.toml              # Dependencies (managed by uv)
│   ├── uv.lock                     # Lockfile untuk reproducible build
│   ├── .python-version             # Versi Python
│   └── Dockerfile                  # Multi-stage build
│
├── web-admin/                      # React + Vite Frontend (SPA)
│   ├── src/
│   │   ├── components/             # Layout.tsx (sidebar+header), Modal.tsx (native <dialog>)
│   │   ├── routes/                 # TanStack Router: login, dashboard, rooms, items, inspections, analytics
│   │   ├── hooks/                  # useAuth, useMasterData, useInspections, useAnalytics
│   │   ├── lib/                    # api.ts (kustom fetch wrapper + auto-refresh)
│   │   ├── main.tsx                # Entry point (Router + Query + Auth setup)
│   │   └── index.css               # Tailwind + Planograph utility classes
│   ├── CONTEXT.md                  # Frontend domain context
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js          # Planograph design tokens (navy, teal, canvas)
│   ├── nginx.conf                  # Proxy /api → backend
│   └── Dockerfile                  # Multi-stage build (Node → Nginx)
│
├── docs/                           # Dokumentasi
│   ├── 00-core-prompt.md
│   ├── 01-database-schema.md
│   ├── 02-prd-server.md
│   ├── 03-project-structure.md     # ← file ini
│   ├── 04-architecture.md          # Arsitektur detail
│   ├── 05-implementation-tracking.md
│   ├── 06-refactoring-tracker.md
│   ├── agents/
│   └── adr/
│
├── CONTEXT-MAP.md                  # Indeks contexts + ADR index + cross-cutting
```

## Aturan

### Frontend (`web-admin/`)
- **React + Vite + TanStack Router + TanStack Query** — kustom UI (Planograph theme, tanpa shadcn/ui)
- Route-based pages di `src/routes/`, komponen reusable di `src/components/`
- Data fetching via custom hooks + TanStack Query di `src/hooks/`
- API Client kustom (`src/lib/api.ts`) untuk auto-refresh token + error handling
- Deploy sebagai static files via Nginx (multi-stage Docker build)
- Domain context: `web-admin/CONTEXT.md`

### Backend (`backend/`)
- **Package manager**: `uv` (bukan pip/poetry) — lihat `docs/04-architecture.md`
- **Arsitektur**: Modular per domain (`modules/auth/`, `modules/inspection/`, dll)
- **Layer per module**: `api.py` → `services.py` → `models.py`
- Uploaded files di `backend/uploads/` (Docker volume)

### Infrastructure (`docker-compose.yml`)
- **Reverse proxy**: Nginx di frontend container — proxy `/api/` ke backend
- **Database**: SQLite + aiosqlite (dev) / PostgreSQL + asyncpg (prod) — ganti via `DATABASE_URL`
- **FastAPI**: backend API di port 8100 (dev), port 80 (container)
- **Nginx**: serve frontend static files + proxy `/api` → `http://backend`

### Context Files
Domain CONTEXT.md sudah co-located dengan kode masing-masing:
- `backend/app/modules/<domain>/CONTEXT.md` — 6 backend contexts
- `web-admin/CONTEXT.md` — frontend context
- `CONTEXT-MAP.md` — indeks semua contexts + cross-cutting concerns
