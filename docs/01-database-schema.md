# DATABASE SCHEMA & LOGIC

**1. Master Data (`rooms`, `inspection_items`)**
- Kolom: `id`, `name`, `is_active` (Boolean, default True), `updated_at` (DateTime timezone, nullable — wajib terisi sejak dibuat via ORM; kolom tetap nullable agar data lama yang belum backfill tidak rusak).
- `updated_at` dibump otomatis oleh service layer (create/update/delete) dan dipakai sync incremental Android (`?since=`).

**1b. Pivot Tables (`room_items`, `user_rooms`)**
- `room_items` (relasi room↔inspection item): `id`, `room_id` (FK), `item_id` (FK), `sort_order` (Integer, default 0 — urutan checklist per ruangan, ADR-0013), `created_at` (DateTime timezone), `is_active` (Boolean, default True), `updated_at` (DateTime timezone, nullable). Unique `(room_id, item_id)`.
- `user_rooms` (relasi user↔room): `id`, `user_id` (FK), `room_id` (FK), `created_at` (DateTime timezone), `is_active` (Boolean, default True), `updated_at` (DateTime timezone, nullable). Unique `(user_id, room_id)`.
- **Soft-delete tombstone (ADR-0009 / ADR-0010):** unassign = `is_active=False` + bump `updated_at`, BUKAN hard delete — supaya sync incremental Android (`?since=` memfilter `updated_at`) bisa mengirim penghapusan relasi. Assign ulang = reaktivasi tombstone (bukan baris baru, unik constraint tetap terjaga). Kolom ditambahkan + backfill `updated_at = created_at` di migrasi `007_soft_delete_pivot_tables`.

**2. Transaksi (`inspections`, `inspection_details`, `inspection_photos`)**
- **Header:** `id`, `room_id`, `inspector_id`, `status` (PENDING/APPROVED/REJECTED), `business_date` (Date), `local_timestamp` (dari Android).
  - `business_date` = `DATE(local_timestamp)` langsung (WIB, tanpa offset). Bukan waktu upload.
- **Idempotency:** Composite Unique Constraint pada `(room_id, local_timestamp, inspector_id)` untuk mencegah duplikasi Lazy Sync.
- **Detail:** `id`, `inspection_id`, `item_id`, `item_name_snapshot` (String), `score` (0-2).
- **Photos:** `id`, `inspection_detail_id` (FK ke inspection_details), `photo_file_name` (String), `thumbnail_file_name` (String, nullable), `sort_order` (Integer, default 0), `created_at` (DateTime dengan timezone via SQLAlchemy).
  - Satu detail bisa punya banyak foto (unlimited).
  - Foto disimpan di filesystem (`uploads/` via Docker volume).

**3. CQRS Analytics (`room_monthly_stats`, `issue_frequency_stats`)**
- Tabel ini hanya di-UPSERT oleh Background Jobs saat inspeksi berubah menjadi APPROVED.
- Dashboard Web HANYA melakukan SELECT ke tabel ini agar performa super cepat.

**4. State Machine (`background_jobs`)**
- Kolom: `id`, `reference_id`, `task_type`, `status` (PENDING, PROCESSING, COMPLETED, FAILED), `payload`, `retry_count` (Integer, default 0), `max_retries` (Integer, default 3).

**5. Scoring Formula**
- Skor% = (Jumlah Skor Didapat) / (Jumlah Item × 2) × 100%
- Skor: 0 (Berisiko — wajib foto), 1 (Minor Defect), 2 (Sesuai Standar).
