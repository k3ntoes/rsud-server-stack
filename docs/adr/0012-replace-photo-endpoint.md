# ADR-0012: Replace Photo Endpoint — PUT /api/inspections/{id}/photos/{photoId}

**Status**: Accepted

Endpoint untuk mengganti file foto pada inspeksi yang **sudah terkirim** ke server. Dependensi fitur re-upload manual Android (ADR-0016 dual-path photo storage, di repo Android).

## Context

Android menyimpan backup lokal foto terkirim di `files/photos_sent`. Ketika foto di server rusak/hilang, petugas perlu re-upload manual. `POST /api/upload` biasa selalu menghasilkan UUID baru yang **tidak terhubung** ke inspeksi — tidak bisa digunakan untuk memperbaiki foto yang sudah terkirim.

Contract `docs/android-to-be-api-contract.md` section 4.6 sudah mendefinisikan endpoint ini, namun bertanda *"Endpoint ini BELUM ada di backend"*. Backend inspection module saat ini tidak memiliki endpoint PUT sama sekali (hanya POST submit, GET list/detail, POST approve/reject).

## Keputusan

### 1. Scope

Endpoint hanya **replace photo yang sudah ada** (`{photoId}` wajib ada). Bukan update inspeksi penuh (tidak ubah score, room, business_date, dst).

### 2. Access Control

Pemilik inspeksi (`inspector_id == current_user.id`) **ATAU** role `admin_ppi`/`supervisor`:

- Skenario utama (Android offline-first) adalah petugas yang sama melakukan re-upload dari backup lokalnya
- Supervisor/admin butuh jalur perbaikan jika petugas tidak bisa melakukannya
- Tidak terbuka ke inspector lain yang kebetulan di-assign ke room yang sama

### 3. Tanpa Restriksi Status

Foto boleh diganti pada status apa pun (PENDING/APPROVED/REJECTED). Foto **tidak memengaruhi analytics** — analytics murni dihitung dari `score` (`recalculate_analytics`). Membatasi ke PENDING saja akan menghambat skenario inti: memperbaiki foto APPROVED yang rusak.

### 4. Cleanup File Lama (Sinkron, Setelah Commit)

Urutan aman:

1. Simpan file baru (UUID baru via `save_upload` — reuse media module)
2. Update DB: `inspection_photos.photo_file_name` → nama baru, `thumbnail_file_name` → null
3. `create_job(db, "generate_thumbnail", photo.id)` — outbox pattern, sebelum commit
4. Commit
5. Hapus **sinkron** file lama + thumbnail lama (`thumb_{old}`) dari filesystem, toleran jika file sudah tidak ada di disk

Jika error terjadi sebelum commit, file lama tetap utuh (rollback aman). UUID per upload membuat pengecekan "direferensikan photo lain" tidak diperlukan — nama file tidak pernah di-reuse.

### 5. Lokasi Kode

Endpoint & service logic di **inspection module** (path domain-nya `/api/inspections/...`), reuse `save_upload()` dari `media.services` (10MB chunked safety net + validasi ekstensi). Thumbnail regenerate via job `generate_thumbnail` yang sudah ada — outbox pattern (`create_job` sebelum commit), sama seperti `submit_inspection`.

### 6. Response & Errors

- **200**: `PhotoOut` — `id` dan `sort_order` tidak berubah, `photo_file_name` baru, `thumbnail_file_name` null (digenerate async)
- **404** `PHOTO_NOT_FOUND` — inspeksi atau photo tidak ada
- **403** — bukan pemilik inspeksi dan bukan supervisor/admin
- **413** `FILE_TOO_LARGE` — file > 10MB (dari `save_upload`)

Format error mengikuti contract 4.5 (`{ detail, code }`).

## Pertimbangan yang Ditolak

| Alternatif | Alasan Ditolak |
|-----------|----------------|
| Hanya pemilik inspeksi | Supervisor/admin perlu jalur perbaikan jika petugas tidak bisa |
| Hanya status PENDING | Tujuan endpoint justru memperbaiki foto terkirim yang rusak (bisa APPROVED) |
| Jangan hapus file lama | Sampah disk menumpuk di `uploads/` |
| Cleanup via background job | Overkill untuk endpoint frekuensi jarang (re-upload manual) |
| Endpoint di media module | Path `/api/inspections/...` milik domain inspection; butuh akses model inspection |
| `PUT /api/inspections/{id}` (update penuh) | Tidak diminta contract; Android hanya butuh replace foto |

## Konsekuensi

- Tidak perlu recalculate analytics — murni dari `score`
- Catatan: mengganti photo tidak otomatis mengubah `inspection.updated_at` — `onupdate` SQLAlchemy hanya aktif saat baris parent `inspections` itu sendiri di-update, bukan saat child `inspection_photos` diubah
- Perlu test baru: happy path, 404 (inspeksi/photo tidak ada), 403 (bukan owner/supervisor), 413 (file terlalu besar)
- Update `docs/android-to-be-api-contract.md`: tandai section 4.6 sudah didesain (masih perlu implementasi)

## Referensi

- Contract: `docs/android-to-be-api-contract.md` section 4.6 & 5 (tabel ringkasan endpoint)
- ADR-0016 (Android): dual-path photo storage — di luar repo ini
- Inspection module: `backend/app/modules/inspection/`
- Media module: `backend/app/modules/media/services.py` (`save_upload`)
- Background jobs: `backend/app/modules/background/services.py` (`create_job`, `generate_thumbnail`)
