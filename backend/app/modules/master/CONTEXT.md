# Context: Master Data

## Responsibility

Manage reference data: rooms (`rooms`), inspection items (`inspection_items`), and their lifecycle via soft-delete.

## Glossary

| Term | Definition |
|------|------------|
| Room | A physical room in RSUD Ajarbarang that gets inspected |
| Inspection Item | A checkable item within a room (e.g., "Kebersihan Lantai") |
| Soft-Delete | Records marked with `is_active = False` instead of hard-deleted |
| Master Data | Core reference tables that drive the inspection system |

## Key Decisions

- Soft-delete only (`is_active` boolean, default True)
- Admin PPI manages CRUD operations
- Deleting a room/item does not affect historical inspection data (snapshot)

## ADRs

See `docs/adr/` in this context directory for master data-specific decisions.
