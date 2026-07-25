# ADR-0003: JWT Layered Auth dengan httpOnly Refresh Cookie

**Status**: Accepted (updated for Android dual delivery)

Sistem autentikasi menggunakan **JWT dua lapis**: Access Token (15 menit) dan Refresh Token (7 hari). Refresh Token divalidasi silang dengan tabel whitelist `user_sessions`.

Keputusan ini diambil untuk menyeimbangkan keamanan dan kemudahan integrasi antara backend FastAPI, Web Admin (React), dan Android Client.

## Key Decisions

### 1. Dual Token — Access + Refresh

- **Access Token** (15 menit) — dikirim via `Authorization: Bearer` header
- **Refresh Token** (7 hari) — digunakan untuk memperpanjang session tanpa re-login
- Token rotation: setiap refresh, token lama di-revoke dan token baru diterbitkan

### 2. Dual Delivery Refresh Token

| Client | Delivery Method | Cara Kirim |
|--------|----------------|------------|
| **Web (browser)** | httpOnly cookie | Cookie otomatis dikirim browser saat request |
| **Android (OkHttp/Retrofit)** | Request body | `{"refresh_token": "eyJ..."}` di POST body |

Backend menerapkan **fallback logic**: cek request body `refresh_token` dulu, jika tidak ada fallback ke httpOnly cookie. Ini membuat satu endpoint melayani kedua klien tanpa perlu conditional routing.

**Mengapa tidak menggunakan header kustom (X-Refresh-Token)?**
- Body field lebih eksplisit dan konsisten dengan pola JSON API
- Tidak ambigu dengan `Authorization: Bearer` yang reserved untuk Access Token
- Lebih mudah di-debug (visible di request body, bukan hidden header)

### 3. Login Response

Semua klien menerima `refresh_token` di response body (selain httpOnly cookie untuk web):

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": { "id": 1, "username": "petugas01", "role": "inspector" }
}
```

### 4. Logout — Revoke via Body Token

Android tidak memiliki httpOnly cookie, sehingga logout mengirim `refresh_token` di request body. Backend merevoke session dari tabel `user_sessions`. Access Token tidak di-blacklist (hanya bertahan 15 menit).

### 5. Master Data Access untuk Mobile (Read-Only)

Endpoint **GET** `/api/rooms` dan **GET** `/api/inspection-items` dapat diakses oleh **semua role terautentikasi** — tidak hanya admin. Master data adalah data referensi yang dibutuhkan oleh Inspector Android untuk inspeksi offline-first.

> **Batas akses**: Read-only untuk non-admin. Endpoint CRUD (POST/PUT/DELETE) tetap hanya untuk Admin PPI (`get_admin_user` dependency).

### 6. Standard Error Response dengan Error Code

Semua error response menyertakan field `code` (selain `detail`) untuk memudahkan Android Interceptor melakukan auto-refresh tanpa parsing string:

```json
{
  "detail": "Token expired",
  "code": "TOKEN_EXPIRED"
}
```

| Error Code | HTTP Status | Implementasi |
|------------|-------------|--------------|
| `TOKEN_EXPIRED` | 401 | ✅ P1 — auth errors (blocking untuk Android auto-refresh) |
| `TOKEN_INVALID` | 401 | ✅ P1 — auth errors |
| `DUPLICATE_INSPECTION` | 409 | ⏳ P2 — planned |
| `FILE_TOO_LARGE` | 413 | ⏳ P3 — planned via Nginx |

**Pertimbangan yang ditolak:**
- **Refresh Token di localStorage** — rentan XSS, token bisa dicuri oleh injected script
- **Session-based auth (server-side session)** — membutuhkan state di server, tidak cocok untuk load balancing
- **Pure stateless JWT** — tidak bisa di-revoke oleh Admin PPI (fitur kill switch)
- **X-Refresh-Token header** — ambiguous dengan Authorization header, kurang eksplisit
- **Blacklist access_token saat logout** — over-engineering karena token hanya 15 menit

**Konsekuensi:**
- httpOnly cookie mencegah XSS token theft untuk web client
- Whitelist `user_sessions` memungkinkan Admin PPI me-revoke session
- Dual delivery memungkinkan Android menggunakan API yang sama tanpa cookie
- Frontend dan backend harus di domain yang sama (cocok dengan setup docker-compose + reverse proxy)
- CSRF protection via `SameSite=Strict` — sudah diterapkan
- Error `code` field memudahkan Android Interceptor auto-refresh

## Referensi

- Lihat `docs/android-to-be-api-contract.md` untuk detail API contract dengan Android
- Lihat `docs/adr/0007-frontend-auth-pattern.md` untuk frontend web auth pattern
- ADR-0007: Frontend Auth Pattern — SessionStorage + Auto-Refresh Token
- `backend/app/modules/auth/services.py` — implementasi refresh_session, create_session