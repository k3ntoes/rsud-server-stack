# ADR-0004: SQLite (Dev) / PostgreSQL (Prod) — Dual-Database Strategy

**Status**: Accepted

Development environment menggunakan **SQLite via aiosqlite** (file-based, zero setup), sementara produksi tetap menggunakan **PostgreSQL via asyncpg**. Perpindahan antar database cukup dengan mengubah satu environment variable `DATABASE_URL`.

Keputusan ini diambil untuk mempercepat iterasi development — tidak perlu menjalankan Docker atau PostgreSQL di lokal — sambil tetap mempertahankan PostgreSQL di produksi untuk reliability, concurrency, dan fitur lanjutan (partial indexes, full-text search, PL/pgSQL untuk state machine).

**Pertimbangan yang ditolak:**

- **PostgreSQL di Docker untuk semua env** — lebih aman (dev/prod parity), tetapi menambah overhead: developer harus install & jalankan Docker, container makan resource, dan startup lebih lambat. Tidak ideal untuk fast iteration.
- **PostgreSQL managed (Supabase/Neon) untuk semua env** — dev/prod parity maksimal, tapi tergantung koneksi internet, ada latency, dan risiko vendor lock-in.
- **SQLite untuk semua env (termasuk prod)** — zero infrastructure, tapi SQLite tidak mendukung concurrency tinggi, tidak ada row-level locking, dan tidak cocok untuk production workload dengan banyak writer concurrent.

**Konsekuensi:**

- **Dev/prod parity risk** — SQLite dan PostgreSQL punya perbedaan: SQLite tidak mengenforce type strictness, tidak punya native `ARRAY`/`JSONB`, dan `func.now()` berperilaku berbeda (tanpa timezone). Mitigasi: SQLAlchemy ORM mengabstraksi perbedaan ini, migration tetap diuji di PostgreSQL sebelum deploy.
- **SQLite-specific config** — perlu `check_same_thread=False` untuk async, dan `PRAGMA foreign_keys=ON` per-connection karena SQLite nonaktifkan FK constraint secara default.
- **Migration harus kompatibel** — semua migration ditulis dengan `sa.DateTime(timezone=True)` (bukan `TIMESTAMPTZ` PostgreSQL native), dan `server_default` menggunakan SQLAlchemy portable functions.
- **Docker tetap untuk prod** — PostgreSQL hanya berjalan di docker-compose production, bukan di dev environment.
