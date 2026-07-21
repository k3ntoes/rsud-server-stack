# Context: Background Jobs

## Responsibility

Manage asynchronous task execution using the Outbox Pattern via a database-backed state machine (SQLite for dev, PostgreSQL for prod).

## Glossary

| Term | Definition |
|------|------------|
| Outbox Pattern | Jobs written to `background_jobs` table, processed asynchronously |
| State Machine | Job status lifecycle: PENDING → COMPLETED / FAILED |
| Self-Healing | Failed jobs can be retried automatically |
| Task Type 1 | Thumbnail generation after image upload |
| Task Type 2 | Analytics UPSERT when inspection status changes to APPROVED |

## Key Decisions

- `background_jobs` table as job queue (outbox pattern) — SQLite dev, PostgreSQL prod
- Status-based state machine with self-healing capability
- Jobs triggered by database state changes (inspection APPROVED, image uploaded)
- Analytics CQRS recalculation runs via this system

## ADRs

See `docs/adr/` in this context directory for background jobs-specific decisions.
