# RSUD Ajibarang — Server Stack

Sistem Informasi Inspeksi Pencegahan dan Pengendalian Infeksi (PPI) untuk RSUD Ajibarang.

**Tech Stack:** FastAPI (Python) · React (Vite) · SQLite (dev) / PostgreSQL (prod) · TanStack Router/Query · Tailwind CSS

## 📋 Prasyarat

| Tool | Versi | Untuk |
|------|-------|-------|
| Python | ≥ 3.12 | Backend |
| Node.js | ≥ 18 | Frontend |
| `uv` | latest | Package manager backend (Python) |
| npm | ≥ 9 | Package manager frontend |

Install `uv` jika belum ada:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 🚀 Setup & Menjalankan

### 1. Clone & masuk direktori

```bash
git clone https://github.com/k3ntoes/rsud-server-stack.git
cd rsud-server-stack
```

### 2. Backend

```bash
cd backend

# Install dependencies
uv sync

# Buat .env (copy dari template)
cp .env.example .env
# Edit .env — ganti JWT_SECRET dengan random key

# Jalankan migrasi database
uv run alembic upgrade head

# Seed admin user
uv run python -m app.modules.auth.seed

# Jalankan server (development)
uv run fastapi dev app/main.py --port 8000
```

Backend berjalan di **http://localhost:8000**.  
Dokumentasi API (Swagger): **http://localhost:8000/docs**

#### Admin default (seed)
| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | admin_ppi |

### 3. Frontend (Web Admin)

Buka terminal baru:

```bash
cd web-admin

# Install dependencies
npm install

# Jalankan development server
npm run dev
```

Frontend berjalan di **http://localhost:5173**.  
Vite dev server otomatis mem-proxy `/api` ke backend (port 8000).

### 4. Akses

Buka **http://localhost:5173** di browser → login dengan `admin` / `admin123`.

---

## 🗂️ Struktur Proyek

```
rsud-server-stack/
├── backend/                        # FastAPI Backend (Python)
│   ├── app/
│   │   ├── main.py                 # Entry point FastAPI
│   │   ├── config.py               # Settings (pydantic-settings)
│   │   ├── core/                   # Shared infrastructure
│   │   │   ├── database.py         #   AsyncSession, engine
│   │   │   ├── security.py         #   JWT, password hashing
│   │   │   └── dependencies.py     #   Global deps
│   │   ├── modules/
│   │   │   ├── auth/               # Autentikasi & otorisasi
│   │   │   ├── master/             # Master data (rooms, items)
│   │   │   ├── inspection/         # Inspeksi PPI
│   │   │   ├── media/              # Upload & serve foto
│   │   │   ├── analytics/          # Dashboard (read-only)
│   │   │   └── background/         # Background jobs (outbox)
│   │   └── alembic/                # Database migrations
│   ├── uploads/                    # Foto (Docker volume)
│   └── Dockerfile                  # Multi-stage production build
│
├── web-admin/                      # React + Vite Frontend
│   ├── src/
│   │   ├── components/             # UI components (Layout, Modal)
│   │   ├── hooks/                  # Custom hooks + TanStack Query
│   │   ├── routes/                 # TanStack Router pages
│   │   └── lib/                    # Utilities (API client)
│   ├── index.html
│   └── package.json
│
└── docs/                           # Dokumentasi arsitektur
```

---

## 🏗️ Arsitektur

### Backend: Modular 3 Layer

Setiap module mengikuti pola **api → services → models**:

```
api.py       → HTTP concerns, validasi input (Pydantic)
services.py  → Business logic, koordinasi data
models.py    → SQLAlchemy ORM, definisi tabel
```

### Autentikasi: JWT Layered (ADR-0003)

- **Access Token**: short-lived (15 menit), dikirim via `Authorization: Bearer`
- **Refresh Token**: httpOnly cookie (7 hari), divalidasi dengan whitelist `user_sessions`
- Auto-refresh: saat API return 401, frontend otomatis merefresh via cookie

### Role-based Access

| Role | Akses |
|------|-------|
| `admin_ppi` | Full — master data, approval, analytics |
| `supervisor` | Approval inspeksi, analytics |
| `inspector` | Submit inspeksi (via Android) |

### Database

- Dev: **SQLite** (file-based, zero setup) via `aiosqlite`
- Prod: **PostgreSQL** via `asyncpg` — ganti `DATABASE_URL` di `.env`
- Migration: Alembic auto-generate dari SQLAlchemy models
- Soft-delete: semua tabel transaksional punya `is_active` (Boolean)

---

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login` | — | Login, dapat access + refresh token |
| POST | `/api/auth/refresh` | Cookie | Refresh access token |
| POST | `/api/auth/logout` | Cookie | Logout, hapus session |
| GET | `/api/auth/me` | Bearer | Informasi user saat ini |
| GET/POST/PUT/DELETE | `/api/rooms` | admin_ppi | CRUD ruangan |
| GET/POST/PUT/DELETE | `/api/inspection-items` | admin_ppi | CRUD item inspeksi |
| POST | `/api/inspections` | Bearer | Submit inspeksi (Android) |
| GET | `/api/inspections` | supervisor+ | List inspeksi (filter: status, room, date) |
| GET | `/api/inspections/{id}` | supervisor+ | Detail inspeksi |
| POST | `.../{id}/approve` | supervisor+ | Setujui inspeksi |
| POST | `.../{id}/reject` | supervisor+ | Tolak inspeksi (body: `rejection_reason`) |
| POST | `/api/upload` | Bearer | Upload foto |
| GET | `/api/media/{file}` | — | Serve foto (untuk `<img>` tag) |
| GET | `/api/analytics/lowest-rooms` | supervisor+ | Ruangan dengan skor terendah |
| GET | `/api/analytics/top-issues` | supervisor+ | Item paling sering bermasalah |

---

## 🧪 Development

### Menjalankan migration baru

```bash
cd backend
uv run alembic revision --autogenerate -m "<description>"
uv run alembic upgrade head
```

### Menambahkan dependency backend

```bash
cd backend
uv add <package-name>
```

### Menambahkan dependency frontend

```bash
cd web-admin
npm install <package-name>
```

### Build frontend production

```bash
cd web-admin
npm run build  # output di web-admin/dist/
```

---

## 🐳 Docker (Production)

```bash
# Build backend
docker build -t rsud-backend ./backend

# Run backend with PostgreSQL
docker run -p 8000:80 -e DATABASE_URL=postgresql+asyncpg://... rsud-backend
```

Docker Compose dan frontend Dockerfile masih dalam pengembangan (Phase 6).

---

## 📚 Dokumentasi Lanjutan

| Dokumen | Isi |
|---------|-----|
| `docs/00-core-prompt.md` | Aturan absolut sistem |
| `docs/01-database-schema.md` | Skema database lengkap |
| `docs/02-prd-server.md` | Product requirement |
| `docs/03-project-structure.md` | Struktur proyek detail |
| `docs/04-architecture.md` | Arsitektur, deployment, env vars |
| `docs/adr/` | Architectural Decision Records |
| `docs/05-implementation-tracking.md` | Tracking pengerjaan per fase |
| `CONTEXT-MAP.md` | Glossary per domain context |

---

## 📄 Lisensi

Hak cipta © RSUD Ajibarang — Proyek internal.
