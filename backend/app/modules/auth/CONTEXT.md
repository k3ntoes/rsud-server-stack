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
Admin PPI can reset any user's password without the old password — used when a user forgets their password. Password baru bisa diinput manual atau di-generate acak oleh sistem. Password ditampilkan dalam bentuk plain text agar admin bisa menyampaikannya ke user.

**User Creation**:
Admin PPI creates Inspector and Supervisor accounts from the web dashboard.

**Revoke**:
Admin action to kill a user's session by removing their refresh token from the whitelist.

**User CRUD**:
Admin PPI can create, list, update, and soft-delete users from the web dashboard. Saat create, admin menentukan username, password initial, dan role (admin_ppi/supervisor/inspector). Saat update, admin bisa mengubah username, role, dan status aktif. Tidak bisa mengubah password user dari halaman manajemen — user harus menggunakan fitur Change Password sendiri.

**Change Password**:
All authenticated users can change their own password via `POST /api/auth/change-password`. Endpoint memvalidasi old password sebelum mengizinkan perubahan. Tidak ada admin reset password — user harus tahu password lama untuk membuat password baru.

**Admin Reset Password**:
Admin PPI tidak bisa mereset password user lain dari halaman manajemen saat ini (P1). Jika user lupa password, solusi saat ini: admin bisa membuat user baru dengan password baru, lalu nonaktifkan user lama.

**401 vs 403**:
FastAPI HTTPBearer returns **401 Unauthorized** (not 403 Forbidden) when Authorization header is missing or token is invalid. 403 digunakan untuk role-based authorization (user authenticated tapi tidak punya akses).

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

## ADRs

See `docs/adr/` for auth-specific decisions:
- ADR-0003: JWT Layered Auth
- ADR-0004: SQLite Development (PYTHONPATH context)
- ADR-0008: User Management & Monitoring
