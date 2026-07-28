# Context: Master Data

## Responsibility

Manage reference data: rooms (`rooms`), inspection items (`inspection_items`), the many-to-many relationship between them (`room_items`), and their lifecycle via soft-delete.

## Glossary

| Term | Definition |
|------|------------|
| Room | A physical room in RSUD Ajibarang that gets inspected |
| Inspection Item | A checkable item that can be assigned to multiple rooms (e.g., "Kebersihan Lantai") |
| Room-Item Assignment | The many-to-many relationship linking a Room to its applicable Inspection Items via `room_items` pivot table |
| Soft-Delete | Records marked with `is_active = False` instead of hard-deleted |
| Master Data | Core reference tables that drive the inspection system |
| Unassigned Item | An Inspection Item that has not been assigned to any Room — valid but not usable in inspections until assigned |
| Assigned Items | The set of Inspection Items linked to a specific Room — these are the items that must be scored during inspection of that Room |

## Key Decisions

- Soft-delete only (`is_active` boolean, default True)
- Admin PPI manages CRUD operations
- Deleting a room/item does not affect historical inspection data (snapshot)
- **Room-Item is many-to-many** — one item can apply to multiple rooms, one room has multiple items
- **New items start unassigned** — admin must explicitly assign items to rooms after creation
- **UI bidirectional** — manage assignments from both room page and item page
- **Validation per room** — only assigned items must be scored during inspection submission

## ADRs

| ADR | Judul |
|-----|-------|
| ADR-0009 | Room-Item Many-to-Many Relationship |

See `docs/adr/0009-room-item-many-to-many.md` for details.
