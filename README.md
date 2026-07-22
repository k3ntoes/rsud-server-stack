# RSUD Ajibarang — Server Stack

Sistem Informasi Inspeksi Pencegahan dan Pengendalian Infeksi (PPI) untuk RSUD Ajibarang.

**Tech Stack:** FastAPI (Python) · React (Vite) · SQLite (dev) / PostgreSQL (prod) · TanStack Router/Query · Tailwind CSS

---

## 📋 Prasyarat

| Tool | Versi | Untuk |
|------|-------|-------|
| Python | ≥ 3.12 | Backend |
| Node.js | ≥ 18 | Frontend |
| `uv` | latest | Package manager backend |
| npm | ≥ 9 | Package manager frontend |
| GNU Make | — | Development automation (`make`) |

Install `uv` jika belum ada:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 🚀 Setup Cepat (Makefile)

```bash
# 1. Clone
git clone https://github.com/k3ntoes/rsud-server-stack.git
cd rsud-server-stack

# 2. Install semua dependensi
make install
make frontend-install

# 3. Setup database + seed demo data
cp backend/.env.example backend/.env    # edit JWT_SECRET jika perlu
make reset                               # migrate + seed

# 4. Jalankan backend & frontend (dua terminal atau make all)
make dev     # terminal 1: backend di :8000
make frontend-dev  # terminal 2: frontend di :5173

# Atau langsung dua-duanya:
make all     # Ctrl+C untuk stop keduanya
```

Buka **http://localhost:5173** → login dengan salah satu akun di bawah.

---

## 👤 Akun Demo (Seed)

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | **admin_ppi** — full akses (CRUD master, approval, analytics) |
| `supervisor` | `supervisor123` | **supervisor** — approval inspeksi, analytics |
| `inspector` | `inspector123` | **inspector** — submit inspeksi (via API/Android) |

Seed juga membuat 6 ruangan, 10 item inspeksi, dan 3 sample inspeksi (2 APPROVED + 1 PENDING) — data analytics sudah terisi.

---

## 🔧 Makefile Commands

### Backend

| Command | Fungsi |
|---------|--------|
| `make install` | Install Python deps (`uv sync`) |
| `make dev` | Jalankan FastAPI di `:8000` |
| `make migrate` | Jalankan migrasi database |
| `make seed` | Seed semua data demo |
| `make reset` | Hapus DB → migrate → seed (start fresh) |

### Frontend

| Command | Fungsi |
|---------|--------|
| `make frontend-install` | Install Node deps (`npm ci`) |
| `make frontend-dev` | Jalankan Vite dev server di `:5173` |
| `make frontend-build` | Build production ke `dist/` |

### Docker

| Command | Fungsi |
|---------|--------|
| `make docker-up` | Build & start semua service |
| `make docker-down` | Stop & hapus volume |
| `make docker-logs` | Stream log semua container |

### Utils

| Command | Fungsi |
|---------|--------|
| `make clean` | Hapus DB, cache, node_modules, dist |
| `make test` | Jalankan test backend |
| `make all` | Backend + frontend bersamaan (Ctrl+C stop keduanya) |

---

## 🗂️ Struktur Proyek

```
rsud-server-stack/
├── backend/                        # FastAPI Backend (Python)
│   ├── app/
│   │   ├── main.py                 # Entry point FastAPI
│   │   ├── config.py               # Settings (pydantic-settings)
│   │   ├── seed.py                 # Seed data komprehensif
│   │   ├── core/
│   │   │   ├── database.py         #   AsyncSession, engine
│   │   │   ├── security.py         #   JWT, password hashing
│   │   │   └── dependencies.py     #   Global deps
│   │   ├── modules/
│   │   │   ├── auth/               # 🔐 Autentikasi & otorisasi
│   │   │   ├── master/             # 🏗️ Master data (rooms, items)
│   │   │   ├── inspection/         # 📋 Inspeksi PPI
│   │   │   ├── media/              # 🖼️ Upload & serve foto
│   │   │   ├── analytics/          # 📊 Dashboard (read-only)
│   │   │   └── background/         # ⚙️ Background jobs (outbox)
│   │   └── alembic/                # Database migrations
│   ├── uploads/                    # Foto (volume mount)
│   ├── docker-entrypoint.sh        # Migrasi + seed otomatis di container
│   └── Dockerfile                  # Multi-stage production build
│
├── web-admin/                      # React + Vite Frontend
│   ├── src/
│   │   ├── components/             # UI components (Layout, Modal)
│   │   ├── hooks/                  # Custom hooks + TanStack Query
│   │   ├── routes/                 # TanStack Router pages
│   │   └── lib/                    # Utilities (API client)
│   ├── Dockerfile                  # Multi-stage: Node build → Nginx
│   ├── nginx.conf                  # Proxy /api ke backend
│   └── package.json
│
├── docker-compose.yml              # PostgreSQL + Backend + Frontend
├── Makefile                        # Development shortcuts
├── .github/workflows/ci.yml        # CI pipeline
│
└── docs/
    ├── 00-core-prompt.md           # Aturan absolut sistem
    ├── 01-database-schema.md       # Skema database
    ├── 04-architecture.md          # Arsitektur detail
    ├── 05-implementation-tracking.md
    └── adr/                        # Architectural Decision Records
```

---

## 🏗️ Arsitektur

### Backend: Modular 3 Layer

```
api.py       → HTTP concerns, validasi input (Pydantic)
services.py  → Business logic, koordinasi data
models.py    → SQLAlchemy ORM, definisi tabel
```

### Autentikasi: JWT Layered (ADR-0003)

- **Access Token**: short-lived (15 menit), dikirim via `Authorization: Bearer`
- **Refresh Token**: httpOnly cookie (7 hari), whitelist `user_sessions`
- Auto-refresh: frontend otomatis merefresh via cookie saat 401

### Role-based Access

| Role | Akses |
|------|-------|
| `admin_ppi` | Full — master data, approval, analytics |
| `supervisor` | Approval inspeksi, analytics |
| `inspector` | Submit inspeksi (via API) |

### Database

- **Dev**: SQLite (`sqlite+aiosqlite:///./rsud.db`) — file-based, zero setup
- **Prod**: PostgreSQL (`postgresql+asyncpg://...`) — ganti `DATABASE_URL` di `.env`
- Migration via Alembic, soft-delete via `is_active`

---

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login` | — | Login |
| POST | `/api/auth/refresh` | Cookie | Refresh token |
| POST | `/api/auth/logout` | Cookie | Logout |
| GET | `/api/auth/me` | Bearer | User info |
| GET | `/api/rooms` | admin_ppi | List ruangan |
| POST | `/api/rooms` | admin_ppi | Tambah ruangan |
| PUT | `/api/rooms/{id}` | admin_ppi | Edit ruangan |
| DELETE | `/api/rooms/{id}` | admin_ppi | Hapus (soft) |
| GET | `/api/inspection-items` | admin_ppi | List item inspeksi |
| POST | `/api/inspection-items` | admin_ppi | Tambah item |
| PUT | `/api/inspection-items/{id}` | admin_ppi | Edit item |
| DELETE | `/api/inspection-items/{id}` | admin_ppi | Hapus (soft) |
| POST | `/api/inspections` | Bearer | Submit inspeksi |
| GET | `/api/inspections` | supervisor+ | List (filter: status, room, date) |
| GET | `/api/inspections/{id}` | supervisor+ | Detail |
| POST | `.../{id}/approve` | supervisor+ | Setujui |
| POST | `.../{id}/reject` | supervisor+ | Tolak (body: `rejection_reason`) |
| POST | `/api/upload` | Bearer | Upload foto |
| GET | `/api/media/{file}` | — | Serve foto |
| GET | `/api/analytics/lowest-rooms` | supervisor+ | Skor terendah per ruangan |
| GET | `/api/analytics/top-issues` | supervisor+ | Item paling sering bermasalah |

---

## 🐳 Docker (Production)

```bash
# Build & start semua service
make docker-up

# Atau manual:
docker compose up --build -d

# Akses frontend: http://localhost:8080
# API: http://localhost:8000/api
# Swagger: http://localhost:8000/docs
```

Services:
- **Frontend**: Nginx (port `:8080`) — serve SPA + proxy `/api` → backend
- **Backend**: FastAPI + entrypoint (migrasi & seed otomatis)
- **Database**: PostgreSQL 16 (port `:5432`)

Volume: `pgdata` (DB persistent) + `uploads` (foto).

---

## 📚 Dokumentasi Lanjutan

| Dokumen | Isi |
|---------|-----|
| `docs/00-core-prompt.md` | Aturan absolut sistem |
| `docs/01-database-schema.md` | Skema database lengkap |
| `docs/02-prd-server.md` | Product requirement |
| `docs/03-project-structure.md` | Struktur proyek detail |
| `docs/04-architecture.md` | Arsitektur, deployment, env vars |
| `docs/05-implementation-tracking.md` | Tracking pengerjaan per fase |
| `docs/adr/` | ADR: Frontend stack, JWT, Multi-photo |
| `CONTEXT-MAP.md` | Glossary per domain context |

---

## 📄 Lisensi

Hak cipta © RSUD Ajibarang — Proyek internal.
