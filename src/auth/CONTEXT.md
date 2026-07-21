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

**User Creation**:
Admin PPI creates Inspector and Supervisor accounts from the web dashboard.

**Revoke**:
Admin action to kill a user's session by removing their refresh token from the whitelist.

## Key Decisions

- JWT stateless layered auth (Access + Refresh Token)
- Refresh Token delivered via httpOnly cookie (not localStorage)
- Refresh Token cross-validated with `user_sessions` table (whitelist)
- Admin PPI has Kill Switch capability to revoke sessions
- Seed Admin PPI via migration; no public registration
- passlib[bcrypt] for password hashing

## ADRs

See `docs/adr/` for auth-specific decisions.
