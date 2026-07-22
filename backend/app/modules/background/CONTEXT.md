# Context: Background Jobs

## Responsibility

Manage asynchronous task execution using the Outbox Pattern via a database-backed state machine (SQLite + aiosqlite for dev, PostgreSQL + asyncpg for prod).

## Glossary

| Term | Definition |
|------|------------|
| Outbox Pattern | Jobs written to `background_jobs` table, processed asynchronously |
| State Machine | Job status lifecycle: PENDING → PROCESSING → COMPLETED / FAILED |
| Self-Healing | Failed jobs can be retried automatically (status back to PENDING) |
| Task Type 1 | `generate_thumbnail` — generate thumbnail setelah image upload |
| Task Type 2 | `recalculate_analytics` — UPSERT `room_monthly_stats` dan `issue_frequency_stats` saat inspection di-APPROVED |
| Background Job | Record di `background_jobs` dengan `task_type`, `payload` (JSON), `status`, `retry_count`, dan `max_retries` |
| Retry Count | `retry_count` — jumlah retry yang sudah dilakukan (integer, default 0) |
| Max Retries | `max_retries` — batas maksimal retry sebelum job dianggap FAILED permanen (integer, default 3) |

## Key Decisions

- **`background_jobs` table** sebagai job queue (outbox pattern) — SQLite dev, PostgreSQL prod
- **Status lifecycle**: PENDING → PROCESSING → COMPLETED / FAILED. Retry: FAILED → PENDING.
- **Dua task type**: `generate_thumbnail` (after upload) dan `recalculate_analytics` (on APPROVED)
- **Analytics recalculation**: UPSERT `room_monthly_stats` per room + `issue_frequency_stats` untuk item score==0
- **Thumbnail generation**: async, mengubah `thumbnail_file_name` di `inspection_photos`
- **Self-healing**: `process_one_job()` loop dengan retry count limit
- **No scheduler daemon** — jobs diproses secara synchronous inline atau via endpoint trigger

## ADRs

See `docs/adr/` for background jobs-specific decisions.
