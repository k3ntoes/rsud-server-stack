# CORE PROMPT: RSUD Ajibarang Server Stack
**Tugas Anda:** Bertindak sebagai Senior Backend & Frontend Engineer.
**Tech Stack:** Python (FastAPI), SQLite (dev) / PostgreSQL (prod) via SQLAlchemy, Web Admin (TBD).

**Aturan Absolut Sistem:**
1. **Skoring:** Skala 0 (Berisiko, wajib foto), 1 (Minor Defect), 2 (Sesuai Standar).
2. **Database:** Fully Normalized (Header-Detail). Dilarang keras menggunakan Hard-Delete, wajib Soft-Delete (`is_active`) dengan *Snapshot Payload* (menyimpan nama item di tabel transaksi).
3. **Waktu:** Wajib Strict UTC. Backend mengekstrak `business_date` dari `local_timestamp` untuk pergeseran shift RSUD.
  - Di SQLite: `DateTime(timezone=True)` — SQLAlchemy menangani konversi.
4. **Auth:** JWT. Short-Lived Access Token + Refresh Token tersimpan di tabel Whitelist (`user_sessions`). Admin bisa melakukan Revoke.
5. **Upload & Media:** Two-Step Upload. Endpoint foto terproteksi, tidak diekspos publik. File original diakses via One-Time Tokenized Route, Thumbnail di-generate asinkron.
6. **Background Tasks:** Menggunakan Outbox Pattern / State Machine (`background_jobs`) untuk rekap analitik (CQRS) dan kompresi gambar agar memiliki fitur *self-healing*.
