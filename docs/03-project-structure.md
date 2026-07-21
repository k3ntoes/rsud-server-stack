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
├── web-admin/                      # React + Vite Frontend
│   ├── src/
│   │   ├── components/             # shadcn/ui components
│   │   ├── pages/                  # TanStack Router pages
│   │   ├── hooks/                  # Custom hooks + TanStack Query
│   │   └── lib/                    # Utilities
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── Dockerfile                  # Multi-stage build (Nginx)
│
├── docs/                           # Dokumentasi
│   ├── 00-core-prompt.md
│   ├── 01-database-schema.md
│   ├── 02-prd-server.md
│   ├── 03-project-structure.md     # ← file ini
│   ├── 04-architecture.md          # Arsitektur detail
│   ├── agents/
│   └── adr/
│
└── src/                            # (akan di-migrasi ke backend/app/modules/)
    ├── auth/
    ├── inspection/
    ├── master/
    ├── analytics/
    ├── media/
    └── background/
```

## Aturan

### Frontend (`web-admin/`)
- **React + Vite + TanStack Router + TanStack Query + shadcn/ui**
- Route-based pages di `src/pages/`, komponen reusable di `src/components/`
- Data fetching via TanStack Query di `src/hooks/`
- Deploy sebagai static files via Nginx (multi-stage Docker build)

### Backend (`backend/`)
- **Package manager**: `uv` (bukan pip/poetry) — lihat `docs/04-architecture.md`
- **Arsitektur**: Modular per domain (`modules/auth/`, `modules/inspection/`, dll)
- **Layer per module**: `api.py` → `services.py` → `models.py`
- Uploaded files di `backend/uploads/` (Docker volume)

### Infrastructure (`docker-compose.yml`)
- **Reverse proxy** (Traefik/Caddy — TBD): handle HTTPS, routing
- **Database**: SQLite (dev) / PostgreSQL (prod) — ganti via `DATABASE_URL` di `.env`
- **FastAPI**: backend API di port 8000
- **Nginx**: serve frontend static files

### Migrasi dari `src/`
Folder `src/` berisi domain CONTEXT.md yang akan dipindahkan ke `backend/app/modules/` seiring implementasi.
