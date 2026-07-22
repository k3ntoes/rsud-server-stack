# ADR-0008: User Management & Monitoring Features

**Status**: Accepted

Menambahkan tiga fitur baru: User CRUD (manajemen pengguna oleh Admin PPI), Change Password (semua role), dan Inspector Performance Monitoring (jumlah inspeksi per inspector).

## Context

Proyek sudah memiliki sistem autentikasi dasar (login, refresh, logout via JWT dual-token) dengan tiga role: `admin_ppi`, `supervisor`, `inspector`. Namun:

1. **Belum ada UI untuk mengelola pengguna** — admin harus menggunakan seed script atau migration untuk menambah user
2. **Belum ada fitur ganti password** — user tidak bisa mengubah password setelah login pertama
3. **Belum ada monitoring kinerja inspector** — supervisor/admin tidak bisa melihat produktivitas inspector

## Keputusan

### 1. User CRUD di `/api/auth/users` (admin only)

| Operasi | Endpoint | Method | Description |
|---------|----------|--------|-------------|
| List users | `/api/auth/users` | GET | Kembalikan semua user (termasuk nonaktif) |
| Create user | `/api/auth/users` | POST | Buat user baru dengan username + password + role |
| Update user | `/api/auth/users/{id}` | PUT | Ubah username, role, atau status aktif |
| Soft-delete | `/api/auth/users/{id}` | DELETE | Set `is_active = False` |

**Mengapa di module auth, bukan module baru?**
- Data user adalah tabel `users` yang sama
- Tidak perlu module terpisah untuk 4 endpoint sederhana
- Konsisten dengan prinsip KISS/YAGNI — satu module auth menangani semua yang berkaitan dengan user identity

**Mengapa `list_users` tidak filter `is_active`?**
- Admin perlu melihat user yang dinonaktifkan untuk audit
- Berbeda dengan `list_rooms` yang filter `is_active` — rooms adalah master data yang tidak perlu menampilkan data terhapus

### 2. Change Password di `/api/auth/change-password`

- Endpoint baru `POST /api/auth/change-password` (any authenticated user)
- Validasi: old password harus cocok sebelum mengizinkan perubahan
- Tidak ada rate limiter (P0 — tambahkan jika ada brute force attack)

**Mengapa tidak ada admin reset password?**
- Prinsip separation of concern: admin mengelola user, user mengelola passwordnya sendiri
- Admin bisa membuat user baru dengan password baru sebagai workaround jika user lupa password
- Fitur admin reset password bisa ditambahkan nanti jika dibutuhkan (P1)

### 3. Inspector Performance

- Endpoint `GET /api/analytics/inspector-performance?year_month=YYYY-MM`
- Query langsung ke tabel `inspections` (JOIN `users`), bukan dari summary table
- Hanya menghitung inspeksi dengan status `APPROVED`
- Menggunakan date-range filter (`business_date >= start AND business_date < end`) — kompatibel SQLite + PostgreSQL

**Mengapa tidak menggunakan summary table (CQRS)?**
- Query sederhana (COUNT + GROUP BY) — tidak perlu pre-computation
- Data tidak sering diakses (beda dengan lowest-rooms/top-issues yang di-load setiap kali dashboard dibuka)

### 4. Frontend: Pengguna Page (`/users`)

- Halaman custom (tidak menggunakan `MasterDataPage` generic) karena user punya field tambahan: role (enum), password (pada create), status aktif
- Modal create: username + password + role selector
- Modal edit: username + role selector + is_active checkbox
- Tidak ada field password di modal edit — admin tidak bisa mereset password user

### 5. Frontend: Inspector Performance Page (`/inspectors`)

- Halaman sederhana dengan bar chart horizontal
- Month selector (YYYY-MM) di header
- Menggunakan komponen bar yang sama dengan halaman analytics

### 6. Frontend: Change Password Modal

- Terletak di `Layout.tsx` — tombol "Ganti Password" di header, di samping tombol "Keluar"
- Modal native `<dialog>` — reuse komponen yang sudah ada
- Form: old password, new password, confirm new password
- Validasi client-side: new password minimal 6 karakter, confirm password harus cocok

## Pertimbangan yang Ditolak

| Alternatif | Alasan Ditolak |
|-----------|----------------|
| Module terpisah untuk User Management | 4 endpoint sederhana — tidak justify module baru (YAGNI) |
| `list_users` filter `is_active` | Admin perlu lihat semua user untuk audit |
| Admin reset password via API | User harus tahu password lama — security measure |
| CQRS summary table untuk inspector performance | Query terlalu sederhana untuk justify pre-computation |
| Inspector performance di dashboard (bukan halaman terpisah) | Dashboard sudah padat — halaman terpisah lebih fokus |
| Change password di halaman terpisah (bukan modal) | Modal lebih cepat diakses, tidak perlu navigasi ke halaman lain |

## Konsekuensi

- Admin bisa menambah/menonaktifkan user tanpa seed script
- User bisa mengubah password sendiri — tidak perlu campur tangan admin
- Supervisor/Admin bisa melihat produktivitas inspector per bulan
- Frontend: 2 halaman baru + 1 modal di layout
- Backend: 4 endpoint user CRUD + 1 change password + 1 inspector performance = 6 endpoint baru
- Unit test: 20 test baru (total test suite: 68 tests)

## Referensi

- ADR-0003: JWT Layered Auth dengan httpOnly Refresh Cookie
- ADR-0007: Frontend Auth Pattern — SessionStorage + Auto-Refresh Token
- `docs/05-implementation-tracking.md` — Phase 7 untuk tracking implementasi
- `backend/app/modules/auth/CONTEXT.md` — glossary dan key decisions auth module
- `backend/app/modules/analytics/CONTEXT.md` — glossary analytics dan inspector performance
