# Context: Authentication & Authorization

## Responsibility

Manage user identity, access control, and session lifecycle for the RSUD Ajibarang system.

## Language

**Supervisor**:
Role that can view pending inspections, view original photos, approve/reject.
_Avoid_: Approver, reviewer

**Admin PPI**:
Role that manages master data, analytics dashboard, and can revoke JWT sessions.
_Avoid_: Super admin, manager

**Inspector**:
Petugas who performs inspections via the Android app.
_Avoid_: Petugas, officer, field agent

**Access Token**:
Short-lived JWT (15 menit) for API authorization.
_Avoid_: Auth token, bearer token

**Refresh Token**:
Long-lived JWT (7 hari) validated against `user_sessions` whitelist, delivered via httpOnly cookie.
_Avoid_: Session token

**Session Whitelist**:
The `user_sessions` table that stores active refresh tokens for cross-validation and admin revoke.

**Seed**:
Initial admin account created via database migration — no self-registration.

**Admin Reset Password**:
Admin PPI can reset any user's password via `PUT /api/auth/users/{user_id}/reset-password` without knowing their old password. All active sessions are revoked on reset (user must re-login). New password is sent in request body. Endpoint returns the new password in plain text so admin can convey it to the user.

**User Creation**:
Admin PPI creates Inspector and Supervisor accounts from the web dashboard.

**Revoke**:
Admin action to kill a user's session by removing their refresh token from the whitelist.

**User CRUD**:
Admin PPI can create, list, update, and soft-delete users from the web dashboard. Saat create, admin menentukan username, nama lengkap (opsional), password initial, dan role (admin_ppi/supervisor/inspector). Saat update, admin bisa mengubah username, nama lengkap (`name`), role, dan status aktif. Tidak bisa mengubah password user dari halaman manajemen — user harus menggunakan fitur Change Password sendiri.

**Change Password**:
All authenticated users can change their own password via `POST /api/auth/change-password`. Endpoint memvalidasi old password sebelum mengizinkan perubahan.

**401 vs 403**:
FastAPI HTTPBearer returns **401 Unauthorized** (not 403 Forbidden) when Authorization header is missing or token is invalid. 403 digunakan untuk role-based authorization (user authenticated tapi tidak punya akses).

**User-Room Assignment**:
Relasi many-to-many antara User dan Room melalui tabel pivot `user_rooms`. User dengan role `inspector` dan `supervisor` di-assign ke room tertentu — menentukan room mana yang bisa mereka inspeksi/approve. Admin PPI tidak perlu di-assign.

**Inspector Room Scope**:
Daftar room yang di-assign ke seorang inspector — hanya room ini yang bisa di-inspeksi oleh petugas tersebut.

**Supervisor Room Scope**:
Daftar room yang di-assign ke seorang supervisor — default filter di halaman approval hanya menampilkan inspeksi dari room ini. Supervisor bisa toggle "Lihat semua room" untuk backup approval.

## Key Decisions

- JWT stateless layered auth (Access + Refresh Token)
- Refresh Token delivered via httpOnly cookie (not localStorage)
- Refresh Token cross-validated with `user_sessions` table (whitelist)
- Admin PPI has Kill Switch capability to revoke sessions
- Seed Admin PPI via migration; no public registration
- `passlib[bcrypt]` for password hashing, pinned to `bcrypt<4.1` — bcrypt>=4.1 removes `__about__` module yang dibutuhkan passlib
- HTTPBearer default behavior: missing/invalid token → 401 (not 403)
- **User CRUD endpoint di `/api/auth/users`** (admin only) karena berkaitan dengan tabel `users` yang sama dengan auth module
- **Change Password endpoint di `/api/auth/change-password`** (any authenticated user) — endpoint terpisah agar tidak bercampur dengan login flow
- **Soft-delete pada user**: status `is_active = False` menonaktifkan user tanpa menghapus data historis inspeksi
- **Pemisahan User CRUD dan Change Password**: Admin mengelola user, user mengelola passwordnya sendiri — prinsip separation of concern
- **`list_users` mengembalikan semua user** (tidak filter `is_active`) — admin perlu melihat user yang dinonaktifkan (berbeda dengan `list_rooms` yang filter `is_active`)
- **User-Room Assignment**: Relasi many-to-many via tabel `user_rooms` terpisah — hanya untuk role `inspector` dan `supervisor`
- **Validasi submission**: Inspector hanya bisa submit inspeksi untuk room yang di-assign
- **Filter approval default**: Supervisor hanya melihat inspeksi untuk room yang di-assign (bisa toggle `show_all`)
- **Migrasi auto-assign**: Semua user inspector & supervisor yang ada akan di-assign ke semua room aktif
- **Bulk sync user-rooms**: Endpoint `GET /api/auth/user-rooms?since=...` mengembalikan semua asosiasi user↔room untuk Android sync (menggunakan `SyncResponse<UserRoomOut>`)
- **User-Room management bidirectional**: Admin bisa manage asosiasi dari halaman User (via `/api/auth/users/{id}/rooms`) atau dari halaman Room (via `/api/auth/rooms/{id}/users`)
- **My Rooms endpoint**: `GET /api/auth/me/rooms?since=...` mengembalikan room yang di-assign ke user login (untuk Android filter UI)

## ADRs

See `docs/adr/` for auth-specific decisions:
- ADR-0003: JWT Layered Auth
- ADR-0004: SQLite Development (PYTHONPATH context)
- ADR-0008: User Management & Monitoring
- ADR-0010: User-Room Assignment
