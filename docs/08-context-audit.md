# Comprehensive CONTEXT Audit — RSUD Ajibarang Server Stack

> **Audit date:** 2026-07-22
> **Scope:** Semua CONTEXT files, docs/ files vs actual implementation code
> **Methodology:** Baca CONTEXT per modul → bandingkan dengan kode implementasi → catat GAP

---

## Summary

| Modul | ✅ Sesuai | ⚠️ Minor | ❌ Gap Kritis |
|-------|----------|----------|-------------|
| 🔐 Auth | 6 | 1 | 0 |
| 🏗️ Master | 3 | 0 | 0 |
| 📋 Inspection | 5 | 1 | 0 |
| 🖼️ Media | 3 | 1 | **1** |
| 📊 Analytics | 4 | **1** | 0 |
| ⚙️ Background | 5 | 0 | 0 |
| 🖥️ Web Admin | 7 | 0 | 0 |
| 📚 Docs | 3 | **2** | 0 |

---

## 🔐 Auth Module

### CONTEXT: `backend/app/modules/auth/CONTEXT.md`

| Claim | Kode | Status |
|-------|------|--------|
| JWT stateless layered auth (Access + Refresh) | `core/security.py` — `create_access_token()`, `create_refresh_token()` | ✅ |
| Refresh Token via httpOnly cookie | `auth/api.py:login()` — `response.set_cookie(httponly=True)` | ✅ |
| Refresh cross-validated `user_sessions` whitelist | `auth/services.py:refresh_session()` — query `UserSession.is_active == True` | ✅ |
| Admin PPI Kill Switch (revoke sessions) | `auth/services.py:revoke_session()` — ada, via `bd update session_id` | ✅ |
| Seed Admin PPI via **database migration** | `auth/seed.py` — **standalone script**, bukan migration | ⚠️ |
| HTTPBearer: missing/invalid → 401 | `core/dependencies.py` — `HTTPException(401)` | ✅ |
| Role-based 403 (bukan 401) | `auth/dependencies.py` — `HTTPException(403)` | ✅ |
| `passlib[bcrypt]`, `bcrypt<4.1` pin | `pyproject.toml` ✅, `core/security.py` ✅ | ✅ |

### ⚠️ Temuan

1. **Seed bukan via migration.** CONTEXT bilang "Seed Admin PPI via database migration — no self-registration", tapi seed admin ada di `auth/seed.py` (standalone) dan `app/seed.py` (komprehensif), bukan via Alembik migration. Dampak: seed tidak otomatis jalan saat `alembic upgrade head`.

---

## 🏗️ Master Module

### CONTEXT: `backend/app/modules/master/CONTEXT.md`

| Claim | Kode | Status |
|-------|------|--------|
| Soft-delete only (`is_active`) | `master/models.py` — `is_active: Mapped[bool] = mapped_column(Boolean, default=True)` | ✅ |
| Admin PPI manages CRUD | `master/api.py` — semua pakai `Depends(get_admin_user)` | ✅ |
| Delete does not affect historical data | Snapshot `item_name_snapshot` di inspection_details | ✅ |

### ✅ Semua sesuai — tidak ada GAP.

---

## 📋 Inspection Module

### CONTEXT: `backend/app/modules/inspection/CONTEXT.md`

| Claim | Kode | Status |
|-------|------|--------|
| Fully normalized header-detail | `inspection/models.py` — Inspection + InspectionDetail + InspectionPhoto | ✅ |
| Composite unique idempotency | `(room_id, local_timestamp, inspector_id)` — `UniqueConstraint` di model | ✅ |
| Snapshot payload (`item_name_snapshot`) | `submit_inspection()` — snapshot dari master items | ✅ |
| `local_timestamp` untuk business date | `business_date` diisi dari `data.business_date` (dari Android) | ✅ |
| `joinedload` + `.unique()` | `inspection/services.py` — `joinedload(Inspection.details).joinedload(...)` + `.unique()` | ✅ |
| All items must be scored | Tidak ada validasi bahwa semua active items di-cover | ⚠️ |
| Approval per-header + mandatory reason | `RejectRequest.rejection_reason` required | ✅ |

### ⚠️ Temuan

1. **Tidak ada validasi "all items required".** CONTEXT bilang: "Every inspection must score all active inspection items assigned to the room. Missing items are rejected at submission." Tapi `submit_inspection()` di `inspection/services.py` hanya iterasi `data.details` tanpa ngecek apakah ada active items yang terlewat. Kalau client hanya kirim 3 dari 10 items, submission tetap sukses.

---

## 🖼️ Media Module

### CONTEXT: `backend/app/modules/media/CONTEXT.md`

| Claim | Kode | Status |
|-------|------|--------|
| Two-Step Upload | `POST /api/upload` terpisah dari `POST /api/inspections` | ✅ |
| Protected photo endpoints (not public) | `/api/media/{filename}` — **TIDAK ADA** auth dependency! | ❌ |
| Original photos via one-time tokenized route | Tidak ada implementasi one-time token | ❌ |
| No server-side size limit | Tidak ada validasi ukuran di `save_upload()` | ✅ |
| Multiple photos per item (`inspection_photos` normalized) | Model `InspectionPhoto` dengan FK ke `inspection_detail_id` | ✅ |
| Local storage via Docker volume | `settings.UPLOAD_DIR = "uploads"` | ✅ |
| Thumbnail async (`generate_thumbnail`) | `background/services.py` — placeholder (no-op) | ⚠️ |

### ❌ Temuan Kritis

1. **`/api/media/{filename}` TANPA AUTH.** Endpoint serve file langsung tanpa pengecekan token/user:
   ```python
   @router.get("/media/{filename}")
   async def serve_file(filename: str):
       # ← Tidak ada auth!
   ```
   Siapa pun yang tahu filename bisa akses foto langsung. CONTEXT bilang "Protected photo endpoints (not publicly exposed)" dan "One-Time Tokenized Route".

2. **One-time token tidak diimplementasi.** Tidak ada mekanisme token sementara untuk akses foto original.

3. **Thumbnail masih placeholder** (sudah di-tracking di GAP sebelumnya).

---

## 📊 Analytics Module

### CONTEXT: `backend/app/modules/analytics/CONTEXT.md`

| Claim | Kode | Status |
|-------|------|--------|
| Dashboard SELECTs ONLY from summary tables | `analytics/services.py` — hanya query `RoomMonthlyStats` dan `IssueFrequencyStats` | ✅ |
| Summary tables UPSERTed by background jobs | `background/services.py:recalculate_analytics()` | ✅ |
| Scoring formula: (actual / max) × 100% | `analytics/api.py` — `round(r.total_score / r.max_score * 100, 1)` | ✅ |
| Two Metrics: lowest rooms + top issues | 2 endpoint: `/lowest-rooms` + `/top-issues` | ✅ |
| **Default view: current week** | Frontend `useAnalytics.ts` default ke **bulan** (`currentMonth()`), API default ke bulan (`%Y-%m`) | ⚠️ |

### ⚠️ Temuan

1. **Default view seharusnya weekly, tapi implementasi monthly.** CONTEXT bilang: "Default dashboard view is weekly, not monthly — filter selector allows changing period." Tapi:
   - `room_monthly_stats` di-group per `year_month` (tidak ada granularity weekly)
   - Frontend `useAnalytics.ts` pakai `currentMonth()` sebagai default
   - API `/lowest-rooms` dan `/top-issues` default ke `datetime.now().strftime("%Y-%m")` (monthly)
   - Tidak ada weekly filter di frontend atau backend

---

## ⚙️ Background Module

### CONTEXT: `backend/app/modules/background/CONTEXT.md`

✅ **Semua GAP sudah diperbaiki** di sesi sebelumnya (docs/07-background-jobs-gaps.md):
- PROCESSING status ✅
- Self-healing retry mechanism ✅
- `generate_thumbnail` handler (placeholder) ✅
- Glossary `retry_count` & `max_retries` ✅
- Migration 005 ✅

---

## 🖥️ Web Admin Frontend

### CONTEXT: `web-admin/CONTEXT.md`

| Claim | Kode | Status |
|-------|------|--------|
| React 18 | `package.json` ✅ | ✅ |
| Vite 6 | `vite.config.ts` ✅ | ✅ |
| TanStack Router | `main.tsx` — `createRouter()` ✅ | ✅ |
| TanStack Query | `main.tsx` — `QueryClientProvider` ✅ | ✅ |
| Tailwind CSS + Planograph | `tailwind.config.js` + `index.css` ✅ | ✅ |
| Modal via native `<dialog>` | `components/Modal.tsx` ✅ | ✅ |
| `sessionStorage` for tokens | `lib/api.ts` — `sessionStorage.getItem("auth_token")` | ✅ |
| Auto-refresh on 401 | `lib/api.ts:tryRefresh()` ✅ | ✅ |
| All pages/routes match | Semua route ada sesuai tabel | ✅ |

### ✅ Semua sesuai — tidak ada GAP.

---

## 📚 Docs & Cross-Cutting

### `docs/00-core-prompt.md`

| Claim | Kode | Status |
|-------|------|--------|
| Tech stack mentions **shadcn/ui** | Frontend **tidak pakai** shadcn/ui — pakai Planograph custom | ⚠️ |
| Scoring 0/1/2 | ✅ | ✅ |
| Database fully normalized | ✅ | ✅ |
| Soft-delete with snapshot | ✅ | ✅ |
| Strict UTC, `DateTime(timezone=True)` | ✅ | ✅ |
| JWT layered auth | ✅ | ✅ |
| Two-Step Upload, one-time token | One-time token **tidak diimplementasi** | ❌ |
| Background tasks outbox pattern | ✅ | ✅ |
| `joinedload` | ✅ | ✅ |
| Dev port 8100 | ✅ | ✅ |

### `docs/01-database-schema.md`

| Claim | Kode | Status |
|-------|------|--------|
| `background_jobs` status: PENDING, COMPLETED, FAILED | Model sekarang punya PROCESSING juga | ⚠️ |
| Tidak mention `retry_count` / `max_retries` | Kolom sudah ada di model & migration 005 | ⚠️ |

### `docs/02-prd-server.md`

| Claim | Kode | Status |
|-------|------|--------|
| Supervisor: lihat PENDING, approve/reject | ✅ | ✅ |
| Admin PPI: dashboard, master data, revoke | ✅ | ✅ |
| Two-Step Upload | ✅ | ✅ |
| Thumbnail gambar **lazy load** | Frontend tidak render thumbnail — hanya nama file | ⚠️ |
| Dashboard CQRS dari summary tables | ✅ | ✅ |

---

## 📋 Ringkasan Semua GAP

| # | Modul | GAP | Severity | File |
|---|-------|-----|----------|------|
| 1 | 🔐 Auth | Seed via standalone script, bukan migration (ber tentangan dengan CONTEXT) | 🟡 Minor | `auth/seed.py` vs Alembic |
| 2 | 📋 Inspection | Tidak ada validasi "all items must be scored" | 🟡 Minor | `inspection/services.py:submit_inspection()` |
| 3 | 🖼️ Media | **`/api/media/{filename}` endpoint tanpa auth** — siapa pun bisa akses foto | 🔴 Kritis | `media/api.py:serve_file()` |
| 4 | 🖼️ Media | One-time token tidak diimplementasi | 🟡 Sedang | Belum ada |
| 5 | 📊 Analytics | Default view weekly → implementasi monthly | 🟡 Sedang | `analytics/api.py`, `useAnalytics.ts` |
| 6 | 📚 Doc | `docs/00-core-prompt.md` masih mention shadcn/ui (tidak dipakai) | 🟡 Minor | `docs/00-core-prompt.md` |
| 7 | 📚 Doc | `docs/01-database-schema.md` tidak update PROCESSING & retry fields | 🟡 Minor | `docs/01-database-schema.md` |
| 8 | 📚 PRD | Thumbnail lazy load di frontend belum ada (cuma nama file) | 🟡 Sedang | `inspection-detail.tsx` |

---

## Prioritas Perbaikan

### 🔴 Priority 1 (Critical — Security)
1. **Media endpoint tanpa auth** — Tambah `Depends(get_current_user)` atau implementasi one-time token

### 🟡 Priority 2 (Medium — Functionality)
2. **Default view weekly** — Ubah frontend + API ke weekly default, atau setidaknya sync docs dengan implementasi
3. **Thumbnail lazy load** — Tampilkan thumbnail sebenarnya (bukan nama file)
4. **One-time token** — Untuk akses foto original via tokenized route

### 🟢 Priority 3 (Low — Docs/Sync)
5. **Seed via migration** — Pindahkan seed admin ke migration atau update CONTEXT
6. **Sync docs** — Update `docs/00-core-prompt.md`, `docs/01-database-schema.md` dengan implementasi terbaru
7. **All items validation** — Validasi bahwa semua active items di-score saat submission

---

## File Audit Reference

| Modul | CONTEXT file | Kode file |
|-------|-------------|-----------|
| 🔐 Auth | `backend/app/modules/auth/CONTEXT.md` | `auth/api.py`, `services.py`, `models.py`, `dependencies.py` |
| 🏗️ Master | `backend/app/modules/master/CONTEXT.md` | `master/api.py`, `services.py`, `models.py` |
| 📋 Inspection | `backend/app/modules/inspection/CONTEXT.md` | `inspection/api.py`, `services.py`, `models.py`, `schemas.py` |
| 🖼️ Media | `backend/app/modules/media/CONTEXT.md` | `media/api.py`, `services.py` |
| 📊 Analytics | `backend/app/modules/analytics/CONTEXT.md` | `analytics/api.py`, `services.py`, `models.py` |
| ⚙️ Background | `backend/app/modules/background/CONTEXT.md` | `background/services.py`, `models.py`, `worker.py` |
| 🖥️ Web Admin | `web-admin/CONTEXT.md` | `lib/api.ts`, `hooks/*`, `routes/*`, `components/*` |
