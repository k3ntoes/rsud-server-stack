# Phase 9: Room-Item & User-Room Many-to-Many

> Status tracker untuk implementasi ADR-0009 (Room-Item Many-to-Many) dan ADR-0010 (User-Room Assignment).

---

## 📋 Claim Order — Urutan Pengerjaan

> **Aturan**: Claim issue dengan `bd update <id> --claim` sebelum mulai. Setelah selesai, `bd update <id> --status done`.

### 🔶 Priority: Phase 9A — Room-Item Many-to-Many (ADR-0009)
**Issue**: `rsud-server-stack-f4p`

| # | Step | Status | Depends On |
|---|------|--------|------------|
| 1 | Backend: Model `RoomItem` + migration `room_items` | ⬜ | ADR-0009 |
| 2 | Backend: Migration (data) auto-assign existing items ke semua room | ⬜ | Step 1 |
| 3 | Backend: Schemas (`RoomItemOut`, `RoomItemAssign`) | ⬜ | Step 1 |
| 4 | Backend: Services — CRUD room-items (list by room, list by item, assign, unassign) | ⬜ | Step 3 |
| 5 | Backend: Sync endpoint `GET /api/room-items?since=` | ⬜ | Step 4 |
| 6 | Backend: Room→Items endpoints (`GET/POST/DELETE /api/rooms/{id}/items`) | ⬜ | Step 4 |
| 7 | Backend: Item→Rooms endpoints (`GET/POST/DELETE /api/inspection-items/{id}/rooms`) | ⬜ | Step 4 |
| 8 | Backend: Update validasi `submit_inspection()` — validasi berdasarkan `room_items` | ⬜ | Step 1 |
| 9 | Frontend: Hooks room-items di `useMasterData.ts` | ⬜ | Step 3 |
| 10 | Frontend: UI Room→Items (assign/unassign items dari halaman Room) | ⬜ | Step 9 |
| 11 | Frontend: UI Item→Rooms (assign/unassign rooms dari halaman Item) | ⬜ | Step 9 |
| 12 | Tests: Backend test room-items CRUD, validasi submission, sync | ⬜ | Step 4, 8 |
| 13 | Tests: Update existing tests (test_submit_inspection — perlu room_items setup) | ⬜ | Step 8 |

### 🔷 Priority: Phase 9B — User-Room Assignment (ADR-0010)
**Issue**: `rsud-server-stack-7sm`

| # | Step | Status | Depends On |
|---|------|--------|------------|
| 1 | Backend: Model `UserRoom` + migration `user_rooms` | ⬜ | ADR-0010 |
| 2 | Backend: Migration (data) auto-assign inspector & supervisor ke semua room | ⬜ | Step 1 |
| 3 | Backend: Schemas (`UserRoomOut`, `UserRoomAssign`) | ⬜ | Step 1 |
| 4 | Backend: Sync endpoint `GET /api/auth/me/rooms?since=` | ⬜ | Step 3 |
| 5 | Backend: Admin endpoints Room→Users (`GET/POST/DELETE /api/rooms/{id}/users`) | ⬜ | Step 3 |
| 6 | Backend: Admin endpoints User→Rooms (`GET/POST/DELETE /api/auth/users/{id}/rooms`) | ⬜ | Step 3 |
| 7 | Backend: Validasi submission — cek `user_rooms` untuk role inspector | ⬜ | Step 1 |
| 8 | Backend: Filter approval `GET /api/inspections` — default room assign, toggle `?show_all=true` | ⬜ | Step 1 |
| 9 | Backend: Update `GET /api/auth/users` — sertakan daftar room IDs | ⬜ | Step 3 |
| 10 | Frontend: Hooks user-rooms | ⬜ | Step 3 |
| 11 | Frontend: UI User→Rooms di halaman Pengguna | ⬜ | Step 10 |
| 12 | Frontend: UI Room→Users di halaman Room | ⬜ | Step 10 |
| 13 | Frontend: Filter toggle "Lihat semua room" di halaman Inspections | ⬜ | Step 8 |
| 14 | Tests: Backend test user-rooms CRUD, validasi submission, filter approval | ⬜ | Step 4, 7, 8 |
| 15 | Tests: Update existing tests | ⬜ | Step 7, 8 |

---

## 🔄 Workflow

```mermaid
graph TD
    A[Claim issue] --> B[Baca CODING-RULES.md]
    B --> C[Graphify query untuk pahami arsitektur]
    C --> D[Implementasi kode]
    D --> E[pytest untuk backend / tsc untuk frontend]
    E --> F{P断言?}
    F -->|Pass| G[bd update --status done]
    F -->|Fail| D
    G --> H[git add + git commit -m \"<pesan>\"]
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

---

## References

- [ADR-0009: Room-Item Many-to-Many](../docs/adr/0009-room-item-many-to-many.md)
- [ADR-0010: User-Room Assignment](../docs/adr/0010-user-room-assignment.md)
- [Master Data CONTEXT](../backend/app/modules/master/CONTEXT.md)
- [Auth CONTEXT](../backend/app/modules/auth/CONTEXT.md)
- [Android API Contract](../docs/android-to-be-api-contract.md)
