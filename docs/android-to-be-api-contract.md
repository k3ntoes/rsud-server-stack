# Android → Backend API Contract

**Tujuan**: Dokumen ini mendefinisikan API contract antara Android Client dan FastAPI Backend. Digunakan oleh tim BE untuk menyesuaikan endpoint yang sudah ada.

**Status**: Draft — perlu direview oleh tim BE.

---

## 1. Perubahan Auth: Dual Delivery Refresh Token

### Latar Belakang

Web Admin menggunakan httpOnly cookie untuk Refresh Token (ADR-0003). **Android tidak bisa membaca httpOnly cookie** — cookie hanya otomatis dikirim oleh browser, bukan oleh OkHttp/Retrofit.

### Perubahan 1.1: Login Response

**Endpoint**: `POST /api/auth/login`

**Response saat ini:**
```json
{
  "access_token": "eyJ...",
  "user": { "id": 1, "username": "petugas01", "role": "inspector" }
}
```

**Response baru:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": { "id": 1, "username": "petugas01", "role": "inspector" }
}
```

- `refresh_token` — **WAJIB** dikembalikan di response body (String)
- httpOnly cookie tetap di-set untuk web browser (backward compatible)
- Android akan menyimpan `refresh_token` di DataStore-Tink (terenkripsi)

### Perubahan 1.2: Refresh Endpoint

**Endpoint**: `POST /api/auth/refresh`

**Request body saat ini:** Tidak ada (Refresh Token dari cookie)

**Request body baru (pilih SATU cara):**

**Opsi A — Body field (direkomendasikan):**
```json
{
  "refresh_token": "eyJ..."
}
```

**Opsi B — Header:**
```
X-Refresh-Token: eyJ...
```

> ⚠️ **Tidak menggunakan `Authorization: Bearer`** untuk Refresh Token karena ambigu dengan Access Token. BE harus membedakan jenis token dari claims, yang rawan error.

**Rekomendasi: Opsi A (body field)** — lebih eksplisit, konsisten dengan pola JSON API.

**Logika:**
1. Web: httpOnly cookie → ambil dari cookie
2. Android: body `{ "refresh_token": "..." }` → ambil dari request body

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

Sama seperti login — `refresh_token` dikembalikan di body untuk Android, httpOnly cookie tetap di-set untuk web.

### Perubahan 1.3: Logout Response

**Endpoint**: `POST /api/auth/logout`

**Request saat ini:** Tidak ada body (hapus cookie)

**Request baru:**
```json
{
  "refresh_token": "eyJ...",
  "access_token": "eyJ..."
}
```

Android mengirim kedua token agar BE bisa menghapus dari whitelist `user_sessions` dan blacklist Access Token.

---

## 2. Master Data API untuk Offline-First

### Perubahan 2.1: Versioning / Sync Support

**Endpoint**: `GET /api/rooms` dan `GET /api/inspection-items`

Android butuh sync incremental. Tambahkan `updated_at` di response.

**Request query params baru:**
```
GET /api/rooms?since=2026-07-23T00:00:00Z
```

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Ruang Rawat Inap A",
      "is_active": true,
      "updated_at": "2026-07-22T10:00:00Z"
    }
  ],
  "synced_at": "2026-07-23T12:00:00Z"
}
```

### Kolom Baru di Database

- `rooms.updated_at` — DATETIME, nullable
- `inspection_items.updated_at` — DATETIME, nullable

Di-update otomatis saat Admin PPI mengubah data via web dashboard.

---

## 2.2. Room-Item Relations Sync

**Endpoint**: `GET /api/room-items`

Mengembalikan semua relasi room↔item. Android membangun mapping lokal (`roomId → [itemId, ...]`) untuk validasi offline.

**Request query params:**
```
GET /api/room-items?since=2026-07-28T00:00:00Z
```

**Response:**
```json
{
  "data": [
    { "id": 1, "room_id": 1, "item_id": 1, "created_at": "2026-07-28T10:00:00Z" },
    { "id": 2, "room_id": 1, "item_id": 2, "created_at": "2026-07-28T10:00:00Z" },
    { "id": 3, "room_id": 2, "item_id": 1, "created_at": "2026-07-28T10:00:00Z" }
  ],
  "synced_at": "2026-07-28T12:00:00Z"
}
```

**Format data per-item:**
| Field | Tipe | Deskripsi |
|-------|------|-----------|
| `id` | int | Primary key relasi |
| `room_id` | int | ID room |
| `item_id` | int | ID inspection item |
| `created_at` | string ISO 8601 | Waktu assignment |

**Alur Sync Room-Items di Android:**

1. Setelah sync rooms & inspection-items, Android panggil `GET /api/room-items`
2. Bangun struktur data lokal:
   ```kotlin
   val roomItemMap: Map<Int, List<Int>> // key: roomId, value: list of itemIds
   ```
3. Saat submit inspeksi offline, gunakan mapping ini untuk validasi item yang wajib di-score
4. Simpan `synced_at` untuk sync periodik berikutnya

> **Catatan**: Endpoint ini **selalu** mengembalikan `SyncResponse` (wrapper `{ data, synced_at }`) — tidak seperti `/api/rooms` dan `/api/inspection-items` yang mengembalikan array biasa tanpa query `?since=`.

---

## 2.3. User-Room Relations Sync (Assigned Rooms)

**Endpoint**: `GET /api/auth/me/rooms`

Mengembalikan daftar room yang di-assign ke user yang sedang login (berdasarkan `user_rooms` pivot). Android hanya menampilkan room yang relevan untuk petugas tersebut.

**Request query params:**
```
GET /api/auth/me/rooms?since=2026-07-28T00:00:00Z
```

**Response:**
```json
{
  "data": [
    { "id": 1, "name": "UGD", "is_active": true, "updated_at": "2026-07-28T10:00:00Z" }
  ],
  "synced_at": "2026-07-28T12:00:00Z"
}
```

**Format data per-room:**
| Field | Tipe | Deskripsi |
|-------|------|-----------|
| `id` | int | ID room |
| `name` | string | Nama room |
| `is_active` | boolean | Status aktif |
| `updated_at` | string ISO 8601 | Waktu update terakhir |

> **Perbedaan dengan `/api/rooms`**: Endpoint ini hanya mengembalikan room yang di-assign ke user yang login. Android tidak perlu filter manual.

**Alur di Android:**

1. Login → dapat `user.id` dan `user.role`
2. Sync rooms: panggil `GET /api/auth/me/rooms?since=...`
3. Simpan daftar room lokal — hanya room ini yang tampil di dropdown/list pemilihan room
4. Jika user adalah `admin_ppi`, endpoint tetap bisa dipanggil (return empty list — admin PPI dapat full list via `/api/rooms`)

---

## 3. Upload & Media

### Perubahan 3.1: Max File Size (Safety Net)

File size limit di server — Android kompres ke 300KB, tapi server tetap perlu safety net:
- **Max file size**: 10MB (jauh di atas 300KB kompresi Android)
- **Return error**: `413 Payload Too Large`

**Implementasi FastAPI (chunked processing — rekomendasi):**
```python
async def upload_file(file: UploadFile = File(...)):
    total_size = 0
    max_size = 10 * 1024 * 1024  # 10MB safety net
    
    async with aiofiles.open(f"uploads/{file.filename}", 'wb') as out_file:
        while chunk := await file.read(64 * 1024):  # 64KB chunks
            total_size += len(chunk)
            if total_size > max_size:
                await out_file.close()
                os.remove(f"uploads/{file.filename}")
                raise HTTPException(status_code=413, detail="File too large. Max 10MB.")
            await out_file.write(chunk)
```

> ⚠️ **Peringatan**: `await file.read()` tanpa chunk bisa menyebabkan memory overflow untuk file besar. Gunakan chunked processing di atas untuk produksi.

**Alternatif: Middleware level (untuk validasi awal via Content-Length):**
```python
class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int):
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return Response(status_code=413, content="File too large")
        return await call_next(request)

app.add_middleware(LimitUploadSizeMiddleware, max_size=10 * 1024 * 1024)
```

**Terbaik: Infrastruktur level (Nginx) untuk produksi:**
```nginx
server {
    client_max_body_size 10M;
}
```

Gunakan kombinasi: **Nginx** untuk first line defense + **Middleware** untuk aplikasi + **Chunked processing** di handler untuk final validation.

### Perubahan 3.2: Upload Response

**Endpoint**: `POST /api/upload`

**Response saat ini:**
```json
{
  "photo_file_name": "uuid-photo.jpg"
}
```

**Response baru (tambah thumbnail info untuk web):**
```json
{
  "photo_file_name": "uuid-photo.jpg",
  "thumbnail_file_name": null,
  "file_size": 284512
}
```

`thumbnail_file_name` = null karena thumbnail digenerate async oleh background job. `file_size` untuk logging Android.

---

## 4. Inspection Submission

### Perubahan 4.1: Submit Inspection Request Body

**Endpoint**: `POST /api/inspections`

**Request body yang akan dikirim Android:**
```json
{
  "room_id": 1,
  "local_timestamp": "2026-07-23T08:30:00Z",
  "business_date": "2026-07-23",
  "details": [
    {
      "item_id": 1,
      "score": 2,
      "photos": ["uuid-photo-1.jpg"]
    },
    {
      "item_id": 2,
      "score": 0,
      "photos": ["uuid-photo-2.jpg", "uuid-photo-3.jpg"]
    }
  ]
}
```

> **Catatan**: `business_date` bersifat opsional — jika tidak dikirim, BE akan mengisi dengan tanggal hari ini. Format: `YYYY-MM-DD`.

Validasi sisi server:
1. `room_id` harus di-assign ke user yang login (via `user_rooms`)
2. Semua item yang terasosiasi dengan room (via `room_items`) harus di-score — **tidak boleh ada yang terlewat**
3. Idempotency key `(room_id, local_timestamp, inspector_id)` — cegah duplikat dari retry

### Perubahan 4.2: Submit Inspection Response

**Response (sesuai `InspectionOut` schema):**
```json
{
  "id": 42,
  "room_id": 1,
  "inspector_id": 1,
  "status": "PENDING",
  "business_date": "2026-07-23",
  "local_timestamp": "2026-07-23T08:30:00Z",
  "rejection_reason": null,
  "created_at": "2026-07-23T08:30:00Z",
  "details": [
    {
      "id": 1,
      "item_id": 1,
      "item_name_snapshot": "Kebersihan Tangan",
      "score": 2,
      "photos": [
        {
          "id": 1,
          "photo_file_name": "uuid-photo-1.jpg",
          "thumbnail_file_name": null,
          "sort_order": 0
        }
      ]
    }
  ]
}
```

| Field | Tipe | Deskripsi |
|-------|------|-----------|
| `id` | int | ID inspeksi (untuk tracking di HistoryScreen) |
| `room_id` | int | ID room tempat inspeksi |
| `inspector_id` | int | ID petugas yang melakukan inspeksi |
| `status` | string | `"PENDING"` / `"APPROVED"` / `"REJECTED"` |
| `business_date` | string | Tanggal bisnis inspeksi (`YYYY-MM-DD`) |
| `local_timestamp` | string ISO 8601 | Timestamp lokal dari Android |
| `rejection_reason` | string/null | Alasan reject (null jika belum di-reject) |
| `created_at` | string ISO 8601 | Waktu inspeksi dibuat di server |
| `details` | array | Array detail item yang di-score |

**Detail Item:**
| Field | Tipe | Deskripsi |
|-------|------|-----------|
| `id` | int | Primary key detail |
| `item_id` | int | ID inspection item |
| `item_name_snapshot` | string | Nama item saat inspeksi (snapshot) |
| `score` | int | Score: 0=risky, 1=minor, 2=standard |
| `photos` | array | Array foto |

**Detail Photo:**
| Field | Tipe | Deskripsi |
|-------|------|-----------|
| `id` | int | Primary key foto |
| `photo_file_name` | string | Nama file foto |
| `thumbnail_file_name` | string/null | Nama file thumbnail (null jika belum digenerate) |
| `sort_order` | int | Urutan tampilan |

> ⚠️ **Tidak ada field `message` atau `detail_count` di response submit** — `detail_count` hanya ada di `InspectionListItem` (response list). Gunakan `details.length` untuk menghitung jumlah item di Android.

> 📌 **Idempotency Key**: `(room_id, local_timestamp, inspector_id)` — `inspector_id` diambil dari `user.id` yang didapat saat login.

### Perubahan 4.3: List Inspections

**Endpoint**: `GET /api/inspections`

**Request query params:**
```
GET /api/inspections?status=PENDING&show_all=true
```

| Parameter | Tipe | Default | Deskripsi |
|-----------|------|---------|-----------|
| `status` | string | (all) | Filter status: `PENDING`, `APPROVED`, `REJECTED` |
| `show_all` | bool | `false` | Untuk supervisor — jika `true`, tampilkan semua room (tidak hanya yang di-assign) |

### Perubahan 4.4: Get Inspection Detail

**Endpoint**: `GET /api/inspections/{id}`

**Response (sesuai `InspectionOut` schema):**
```json
{
  "id": 42,
  "room_id": 1,
  "inspector_id": 5,
  "status": "PENDING",
  "business_date": "2026-07-23",
  "local_timestamp": "2026-07-23T08:30:00Z",
  "rejection_reason": null,
  "created_at": "2026-07-23T08:30:00Z",
  "details": [
    {
      "id": 1,
      "item_id": 1,
      "item_name_snapshot": "Kebersihan Tangan",
      "score": 2,
      "photos": [
        {
          "id": 1,
          "photo_file_name": "uuid-photo-1.jpg",
          "thumbnail_file_name": null,
          "sort_order": 0
        }
      ]
    }
  ]
}
```

| Field | Tipe | Deskripsi |
|-------|------|-----------|
| `id` | int | ID inspeksi |
| `room_id` | int | ID room |
| `inspector_id` | int | ID petugas |
| `status` | string | `"PENDING"` / `"APPROVED"` / `"REJECTED"` |
| `business_date` | string | Tanggal bisnis (`YYYY-MM-DD`) |
| `local_timestamp` | string ISO 8601 | Timestamp dari Android |
| `rejection_reason` | string/null | Alasan reject |
| `created_at` | string ISO 8601 | Waktu dibuat di server |
| `details` | array | Detail item yang di-score |

> ⚠️ **Tidak ada field `room_name`, `inspector_name`, atau `detail_count` di response ini.**  
> Android harus melakukan lookup dari data yang sudah di-sync secara lokal:
> - `room_name` → lookup dari `rooms` (key: `room_id`)  
> - `inspector_name` → lookup dari `users` (key: `inspector_id`, sync via `GET /api/auth/users`)  
> - `detail_count` → `details.length`

---

## 4.5. Standard Error Response Format

Android Interceptor perlu mendeteksi 401 untuk trigger auto-refresh. Gunakan format error response yang konsisten:

**401 Unauthorized (token expired):**
```json
{
  "detail": "Token expired",
  "code": "TOKEN_EXPIRED"
}
```

**401 Unauthorized (token invalid):**
```json
{
  "detail": "Invalid token",
  "code": "TOKEN_INVALID"
}
```

**413 Payload Too Large:**
```json
{
  "detail": "File too large. Max 10MB.",
  "code": "FILE_TOO_LARGE"
}
```

**409 Conflict (duplicate inspection):**
```json
{
  "detail": "Duplicate inspection",
  "code": "DUPLICATE_INSPECTION"
}
```

**409 Conflict (duplicate assignment):**
```json
{
  "detail": "Already assigned or invalid room/item",
  "code": "DUPLICATE_ASSIGNMENT"
}
```

> Android menggunakan `code` field (bukan `detail`) untuk logika Interceptor — lebih stabil daripada parsing string.

---

## 5. Ringkasan Semua Endpoint Android

| Method | Endpoint | Frekuensi | Auth | Catatan |
|--------|----------|-----------|------|---------|
| POST | `/api/auth/login` | Setiap buka app | None | Return `access_token` + `refresh_token` |
| POST | `/api/auth/refresh` | Tiap 15 menit | Bearer | Cookie (web) + body `{ refresh_token }` (Android) |
| POST | `/api/auth/logout` | Logout manual | Bearer | Kirim `refresh_token` di body |
| GET | `/api/rooms` | Periodik | Bearer | Dukung `?since=` |
| GET | `/api/inspection-items` | Periodik | Bearer | Dukung `?since=` |
| **GET** | **`/api/room-items`** | **Periodik** | **Bearer** | **Sync relasi room↔item — selalu `?since=`** |
| **GET** | **`/api/auth/me/rooms`** | **Periodik** | **Bearer** | **Room yg di-assign ke user login — dukung `?since=`** |
| POST | `/api/upload` | Per foto (≤ 300KB) | Bearer | Multipart/form-data |
| POST | `/api/inspections` | Per inspeksi selesai | Bearer | Validasi room_items + user_rooms |
| GET | `/api/inspections` | Riwayat | Bearer | `?status=` filter, `?show_all=` untuk supervisor |
| GET | `/api/inspections/{id}` | Detail | Bearer | Untuk HistoryScreen |

**Alur Sync Master Data (urutan benar):**

```
1. GET /api/rooms?since=<ts>         → data rooms
2. GET /api/inspection-items?since=<ts> → data items
3. GET /api/room-items?since=<ts>    → mapping room ↔ item (built lokal: roomId → [itemIds])
4. GET /api/auth/me/rooms?since=<ts> → room yg di-assign ke user (filter UI)
```

> **Catatan**: `GET /api/rooms` mengembalikan **semua** room aktif. `GET /api/auth/me/rooms` mengembalikan **hanya** room yang di-assign ke user login. Android sync keduanya — gunakan `/api/auth/me/rooms` untuk filter UI, gunakan `/api/rooms` untuk mapping nama room di data historis.

---

## 6. Prioritas Implementasi

| Prioritas | Item | Effort | Alasan |
|-----------|------|--------|--------|
| **P1** | Login + Refresh dual delivery | Sedang | **Blocking** — Android tidak bisa login/token refresh |
| **P1** | Logout dengan body token | Kecil | Blocking untuk logout flow |
| **P2** | Room-Items sync (`/api/room-items`) | Kecil | Android perlu mapping room→item untuk validasi offline |
| **P2** | User-Rooms sync (`/api/auth/me/rooms`) | Kecil | Android perlu filter room per petugas |
| **P2** | Master Data `updated_at` + `since` | Kecil | Optimasi sync, bisa ditunda (full download dulu) |
| **P3** | Submit inspeksi dengan validasi room_items + user_rooms | Kecil | Backend sudah implementasi — Android perlu update body request |
| **P3** | File size limit (10MB) | Kecil | Safety net, bisa ditunda |
| **P3** | Upload response tambahan | Kecil | Informasi tambahan, tidak blocking |

---

## 7. Lampiran: Perubahan ADR BE

Dokumentasi perubahan di ADR BE:

### ADR-0003 (JWT Layered Auth) — Perlu Update

Tambahkan baris di Key Decisions:
> **Dual Delivery Refresh Token** — Web menerima Refresh Token via httpOnly cookie, Android menerima via response body dan mengirim via Authorization header / request body.

### ADR-0009 — Room-Item Many-to-Many (Phase 9A)

Endpoint sync room-items untuk Android:
- `GET /api/room-items?since=...` — semua relasi room↔item
- `GET /api/rooms/{id}/items` — items per room
- `GET /api/inspection-items/{id}/rooms` — rooms per item

Validasi submission berubah: dari "semua active items" → "items yang terasosiasi dengan room".

### ADR-0010 — User-Room Assignment (Phase 9B)

Endpoint sync untuk assigned rooms per user:
- `GET /api/auth/me/rooms?since=...` — room yang di-assign ke user login
- Inspector hanya bisa submit ke room yang di-assign
- Supervisor hanya melihat room yang di-assign secara default (`?show_all=true` untuk override)

### ADR Baru: Dual Delivery Auth

Jika diperlukan, buat ADR-0011 dengan judul *"Dual Delivery Refresh Token — Cookie for Web, Body for Android"*.
