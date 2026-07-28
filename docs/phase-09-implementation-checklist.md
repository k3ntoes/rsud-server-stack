# Phase 9: Room-Item & User-Room Many-to-Many

> Status tracker untuk implementasi ADR-0009 (Room-Item Many-to-Many) dan ADR-0010 (User-Room Assignment).

---

## 📋 Claim Order — Urutan Pengerjaan

> **Aturan**: Claim issue dengan `bd update <id> --claim` sebelum mulai. Setelah selesai, `bd update <id> --status closed`.

### 🔶 Priority: Phase 9A — Room-Item Many-to-Many (ADR-0009)
**Issue**: `rsud-server-stack-f4p`

| # | Step | Status | Depends On |
|---|------|--------|------------|
| 1 | Backend: Model `RoomItem` + migration `room_items` | 🟢 Done | ADR-0009 |
| 2 | Backend: Migration (data) auto-assign existing items ke semua room | 🟢 Done | Step 1 |
| 3 | Backend: Schemas (`RoomItemOut`, `RoomItemAssign`) | 🟢 Done | Step 1 |
| 4 | Backend: Services — CRUD room-items (list by room, list by item, assign, unassign) | 🟢 Done | Step 3 |
| 5 | Backend: Sync endpoint `GET /api/room-items?since=` | 🟢 Done | Step 4 |
| 6 | Backend: Room→Items endpoints (`GET/POST/DELETE /api/rooms/{id}/items`) | 🟢 Done | Step 4 |
| 7 | Backend: Item→Rooms endpoints (`GET/POST/DELETE /api/inspection-items/{id}/rooms`) | 🟢 Done | Step 4 |
| 8 | Backend: Update validasi `submit_inspection()` — validasi berdasarkan `room_items` | 🟢 Done | Step 1 |
| 9 | Frontend: Hooks room-items di `useMasterData.ts` | 🟢 Done | Step 3 |
| 10 | Frontend: UI Room→Items (assign/unassign items dari halaman Room) | 🟢 Done | Step 9 |
| 11 | Frontend: UI Item→Rooms (assign/unassign rooms dari halaman Item) | 🟢 Done | Step 9 |
| 12 | Tests: Backend test room-items CRUD, validasi submission, sync | 🟢 Done | Step 4, 8 |
| 13 | Tests: Update existing tests (test_submit_inspection — perlu room_items setup) | 🟢 Done | Step 8 |

### 🔷 Priority: Phase 9B — User-Room Assignment (ADR-0010)
**Issue**: `rsud-server-stack-7sm`

| # | Step | Status | Depends On |
|---|------|--------|------------|
| 1 | Backend: Model `UserRoom` + migration `user_rooms` | 🟢 Done | ADR-0010 |
| 2 | Backend: Migration (data) auto-assign inspector & supervisor ke semua room | 🟢 Done | Step 1 |
| 3 | Backend: Schemas (`UserRoomOut`, `UserRoomAssign`) | 🟢 Done | Step 1 |
| 4 | Backend: Sync endpoint `GET /api/auth/me/rooms?since=` | 🟢 Done | Step 3 |
| 5 | Backend: Admin endpoints Room→Users (`GET/POST/DELETE /api/rooms/{id}/users`) | 🟢 Done | Step 3 |
| 6 | Backend: Admin endpoints User→Rooms (`GET/POST/DELETE /api/auth/users/{id}/rooms`) | 🟢 Done | Step 3 |
| 7 | Backend: Validasi submission — cek `user_rooms` untuk role inspector | 🟢 Done | Step 1 |
| 8 | Backend: Filter approval `GET /api/inspections` — default room assign, toggle `?show_all=true` | 🟢 Done | Step 1 |
| 9 | Backend: Update `GET /api/auth/users` — sertakan daftar room IDs | 🟢 Done | Step 3 |
| 10 | Frontend: Hooks user-rooms | 🟢 Done | Step 3 |
| 11 | Frontend: UI User→Rooms di halaman Pengguna | 🟢 Done | Step 10 |
| 12 | Frontend: UI Room→Users di halaman Room | 🟢 Done | Step 10 |
| 13 | Frontend: Filter toggle \"Lihat semua room\" di halaman Inspections | 🟢 Done | Step 8 |
| 14 | Tests: Backend test user-rooms CRUD, validasi submission, filter approval | 🟢 Done | Step 4, 7, 8 |
| 15 | Tests: Update existing tests | 🟢 Done | Step 7, 8 |

---

## 🔄 Workflow

```mermaid
graph TD
    A[Claim issue] --> B[Baca CODING-RULES.md]
    B --> C[Graphify query untuk pahami arsitektur]
    C --> D[Implementasi kode]
    D --> E[pytest untuk backend / tsc untuk frontend]
    E --> F{Pass?}
    F -->|Pass| G[bd update --status closed]
    F -->|Fail| D
    G --> H[git add + git commit -m "<pesan>"]
    H --> I[Lanjut step berikutnya]
```

## Git Commit Convention

```
feat(phase-9a): add RoomItem model and migration
feat(phase-9a): add room-items sync endpoint
feat(phase-9a): update inspection validation for per-room items
feat(phase-9a): add room-items frontend UI
feat(phase-9b): add UserRoom model and migration
feat(phase-9b): add user-room sync and CRUD endpoints
feat(phase-9b): add inspector room validation
feat(phase-9b): add supervisor approval filter
```
