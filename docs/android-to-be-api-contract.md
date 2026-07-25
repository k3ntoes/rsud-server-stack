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

**Endpoint**: `GET /api/master/rooms` dan `GET /api/master/inspection-items`

Android butuh sync incremental. Tambahkan `updated_at` di response.

**Request query params baru:**
```
GET /api/master/rooms?since=2026-07-23T00:00:00Z
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

### Alur Sync Android:

1. Android simpan `last_sync_timestamp` di SharedPreferences/Room
2. Saat sync, kirim `?since=<last_sync_timestamp>`
3. Server return hanya data yang berubah sejak timestamp tersebut
4. Android upsert ke Room lokal

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

Tidak ada perubahan besar — BE sudah mendukung struktur ini. Konfirmasi bahwa:

1. `local_timestamp` diterima sebagai string ISO 8601
2. `details[].photos` adalah array string (`photo_file_name` dari upload endpoint)
3. Idempotency key `(room_id, local_timestamp, inspector_id)` terekstrak dari JWT + body

### Perubahan 4.2: Submit Inspection Response

**Response baru:**
```json
{
  "id": 42,
  "status": "PENDING",
  "message": "Inspeksi berhasil dikirim"
}
```

Android perlu `id` untuk tracking status di HistoryScreen.

> 📌 **Idempotency Key**: `(room_id, local_timestamp, inspector_id)` — `inspector_id` diambil dari `user.id` yang didapat saat login. Pastikan `inspector_id` di JWT claims atau tersedia di login response.

---

## 4.3. Standard Error Response Format

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

> Android menggunakan `code` field (bukan `detail`) untuk logika Interceptor — lebih stabil daripada parsing string.

---

## 5. Ringkasan Semua Endpoint Android

| Method | Endpoint | Frekuensi | Auth | Catatan |
|--------|----------|-----------|------|---------|
| POST | `/api/auth/login` | Setiap buka app | None | Return `access_token` + `refresh_token` |
| POST | `/api/auth/refresh` | Tiap 15 menit | Bearer | Cookie (web) + body `{ refresh_token }` (Android) |
| POST | `/api/auth/logout` | Logout manual | Bearer | Kirim `refresh_token` di body |
| GET | `/api/master/rooms` | Periodik | Bearer | Dukung `?since=` |
| GET | `/api/master/inspection-items` | Periodik | Bearer | Dukung `?since=` |
| POST | `/api/upload` | Per foto (≤ 300KB) | Bearer | Multipart/form-data |
| POST | `/api/inspections` | Per inspeksi selesai | Bearer | Idempotency key |
| GET | `/api/inspections` | Riwayat | Bearer | ?status= untuk filter |
| GET | `/api/inspections/{id}` | Detail | Bearer | Untuk HistoryScreen |

---

## 6. Prioritas Implementasi

| Prioritas | Item | Effort | Alasan |
|-----------|------|--------|--------|
| **P1** | Login + Refresh dual delivery | Sedang | **Blocking** — Android tidak bisa login/token refresh |
| **P1** | Logout dengan body token | Kecil | Blocking untuk logout flow |
| **P2** | Master Data `updated_at` + `since` | Kecil | Optimasi sync, bisa ditunda (full download dulu) |
| **P3** | File size limit (10MB) | Kecil | Safety net, bisa ditunda |
| **P3** | Upload response tambahan | Kecil | Informasi tambahan, tidak blocking |

---

## 7. Lampiran: Perubahan ADR BE

Dokumentasi perubahan di ADR BE:

### ADR-0003 (JWT Layered Auth) — Perlu Update

Tambahkan baris di Key Decisions:
> **Dual Delivery Refresh Token** — Web menerima Refresh Token via httpOnly cookie, Android menerima via response body dan mengirim via Authorization header / request body.

### ADR Baru: Dual Delivery Auth

Jika diperlukan, buat ADR-0009 dengan judul *"Dual Delivery Refresh Token — Cookie for Web, Header for Android"*.
