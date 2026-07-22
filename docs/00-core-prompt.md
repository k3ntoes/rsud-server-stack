# CORE PROMPT: RSUD Ajibarang Server Stack

**Tugas Anda:** Bertindak sebagai Senior Backend & Frontend Engineer.
**Tech Stack:** Python (FastAPI), SQLite + aiosqlite (dev) / PostgreSQL + asyncpg (prod) via SQLAlchemy 2.0 async, Web Admin React + Vite + TanStack + Planograph UI (custom Tailwind).

**Aturan Absolut Sistem:**

1. **Skoring:** Skala 0 (Berisiko, wajib foto), 1 (Minor Defect), 2 (Sesuai Standar).
2. **Database:** Fully Normalized (Header-Detail). Dilarang keras menggunakan Hard-Delete, wajib Soft-Delete (`is_active`) dengan *Snapshot Payload* (menyimpan nama item di tabel transaksi).
   - Dev: SQLite + aiosqlite (`DATABASE_URL=sqlite+aiosqlite:///./rsud.db`)
   - Prod: PostgreSQL + asyncpg (`DATABASE_URL=postgresql+asyncpg://user:pass@host/db`)
   - Migration (Alembic) harus kompatibel dengan kedua engine.
   - **Jalankan command dengan `PYTHONPATH=.`** — uv tidak menambahkan cwd ke Python path secara default.
3. **Waktu:** Wajib Strict UTC. Backend mengekstrak `business_date` dari `local_timestamp` untuk pergeseran shift RSUD.
   - Di SQLite: `DateTime(timezone=True)` — SQLAlchemy menangani konversi.
4. **Auth:** JWT. Short-Lived Access Token (15 menit) + Refresh Token (7 hari, httpOnly cookie) tersimpan di tabel Whitelist (`user_sessions`). Admin bisa melakukan Revoke.
   - Password: `passlib[bcrypt]` dengan `bcrypt<4.1` (bcrypt>=4.1 tidak kompatibel dengan passlib).
   - HTTPBearer: missing/invalid token → 401 (bukan 403).
5. **Upload & Media:** Two-Step Upload. Endpoint foto terproteksi, tidak diekspos publik. File original diakses via One-Time Tokenized Route, Thumbnail di-generate asinkron (task: `generate_thumbnail`).
6. **Background Tasks:** Menggunakan Outbox Pattern (tabel `background_jobs`) dengan state machine (PENDING → PROCESSING → COMPLETED/FAILED). Dua task type: `recalculate_analytics` dan `generate_thumbnail`.
7. **ORM Strategy:** WAJIB `joinedload` untuk eager loading relasi di async context. `selectinload` menyebabkan `MissingGreenlet` pada aiosqlite. Gunakan `.unique()` setelah execute untuk deduplikasi hasil JOIN.
8. **Testing:** pytest + pytest-asyncio, in-memory SQLite (`sqlite+aiosqlite://`), dependency override pattern (`app.dependency_overrides[get_db]`), httpx AsyncClient. 35 unit test (auth, master, inspection).
9. **Dev Port:** Backend API di port **8100** (port 8000 digunakan Portainer di host). Docker compose mapping: `8100:80`.
10. **Tooling:** `make dev` untuk backend, `make frontend-dev` untuk Vite, `make test` untuk unit test. Selalu gunakan `PYTHONPATH=.` sebelum `uv run`.
