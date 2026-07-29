# Context: Analytics

## Responsibility

Provide CQRS-based aggregated data for the Web Dashboard via pre-computed summary tables.

## Language

**CQRS**:
Command Query Responsibility Segregation — write and read models are separate.

**room_monthly_stats**:
Pre-computed monthly stats per room. Columns: `room_id`, `year_month`, `total_score`, `max_score`, `percentage`, `inspection_count`.

**issue_frequency_stats**:
Frequency table for items scoring 0 (Berisiko). Used to identify the most problematic items. Columns: `item_id`, `item_name`, `year_month`, `frequency`.

**Score Formula**:
`Skor% = (Jumlah Skor Didapat) / (Skor Maksimal) × 100%` where max skor = jumlah item × 2.

**Dashboard**:
Web UI powered by 1 dedicated endpoint: `GET /api/analytics/dashboard?year_month=YYYY-MM`. Returns 4 stats in 1 call: pending_count, total_rooms, monthly_inspection_count, avg_score_pct. (ADR-0011)

**Inspector Performance**:
Jumlah inspeksi APPROVED per inspector per bulan. Dihitung via query langsung ke tabel `inspections` (JOIN dengan `users`). Endpoint: `GET /api/analytics/inspector-performance?year_month=YYYY-MM`.

**Filter Date**:
Menggunakan date-range filter (`>= start_of_month, < next_month`) untuk kompatibilitas cross-DB (SQLite + PostgreSQL).

## Key Decisions

- **Dashboard endpoint dedicated**: 4 card statistik dalam 1 panggilan (`GET /api/analytics/dashboard`) — 3 aggregate query (COUNT, SUM), tidak ada N+1 (ADR-0011)
- Summary tables (`room_monthly_stats`) digunakan oleh komponen analitik lain (lowest-rooms, top-issues)
- Summary tables UPSERTed by background jobs when inspection status changes to APPROVED
- Scoring formula: (actual / max) × 100%
- Analytics recalculation triggered via `background_jobs` table (outbox pattern)
- Summary data grouped by `year_month` (format: `YYYY-MM`), dashboard filter menentukan periode tampilan
- **Inspector Performance query langsung ke `inspections`** — tidak perlu summary table karena query sederhana (COUNT + GROUP BY)
- **Date-range filter** digunakan sebagai ganti `.like()` untuk kompatibilitas PostgreSQL

## ADRs

| ADR | Judul |
|-----|-------|
| ADR-0011 | Dashboard Dedicated Endpoint — satu endpoint untuk 4 card statistik dashboard |
| ADR-0008 | User Management & Monitoring (Inspector Performance) |

See `docs/adr/` for analytics-specific decisions.
