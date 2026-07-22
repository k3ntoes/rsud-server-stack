# Context: Inspection

## Responsibility

Handle the core inspection workflow: submission, scoring, approval, and rejection of daily hygiene inspections.

## Language

**Inspection**:
A header record for a room inspection session. Status workflow: PENDING → APPROVED / REJECTED.

**Inspection Detail**:
Line items with item scores, photos, and `item_name_snapshot` for historical accuracy.

**Inspection Photo**:
Photos belonging to an inspection detail, stored in the `inspection_photos` table. Unlimited photos per item.

**Score**:
0 (Berisiko — wajib foto), 1 (Minor Defect), 2 (Sesuai Standar).

**Status**:
PENDING → APPROVED / REJECTED lifecycle. Managed server-side.

**Business Date**:
Date extracted from the Android `local_timestamp` (WIB), used for shift-level reporting. This is the time the inspection was performed, not the time it was uploaded.

**local_timestamp**:
Timestamp sent by the Android app indicating when the inspection was actually performed. Used to derive `business_date` and as part of the idempotency key.

**All Items Required**:
Every inspection must score all active inspection items assigned to the room. Missing items are rejected at submission.

**Approval per-header**:
Supervisor approves or rejects the entire inspection at once. Rejection requires a mandatory reason.

**Idempotency**:
Composite unique key `(room_id, local_timestamp, inspector_id)` prevents duplicate lazy-sync submissions.

**MissingGreenlet**:
Error yang muncul saat `selectinload` digunakan di async context (aiosqlite tidak mendukung concurrent query). Solusi: gunakan `joinedload`.

## Key Decisions

- Fully normalized header-detail structure
- Composite unique constraint for idempotent lazy sync from Android
- Snapshot payload: `item_name_snapshot` stored in detail table
- Use `local_timestamp` (not upload time) for business date
- All items must be scored per inspection
- Approval per-header with mandatory rejection reason
- **Wajib menggunakan `joinedload`** untuk eager loading relasi di async context — `selectinload` menyebabkan `MissingGreenlet` pada aiosqlite. Gunakan `.unique()` untuk deduplikasi hasil JOIN. (Lihat ADR-0005)
- Setelah commit, refetch inspection dengan `joinedload` chain — `db.refresh()` tidak load relasi secara default

## ADRs

See `docs/adr/` for inspection-specific decisions:
- ADR-0005: Async ORM Strategy — joinedload over selectinload
