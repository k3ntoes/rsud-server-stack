# Context: Analytics

## Responsibility

Provide CQRS-based aggregated data for the Web Dashboard via pre-computed summary tables.

## Language

**CQRS**:
Command Query Responsibility Segregation — write and read models are separate.

**room_monthly_stats**:
Pre-computed monthly stats per room. Default dashboard view is weekly, not monthly — filter selector allows changing period. Columns: `room_id`, `year_month`, `total_score`, `max_score`, `percentage`.

**issue_frequency_stats**:
Frequency table for items scoring 0 (Berisiko). Used to identify the most problematic items. Columns: `item_id`, `item_name`, `year_month`, `frequency`.

**Score Formula**:
`Skor% = (Jumlah Skor Didapat) / (Skor Maksimal) × 100%` where max skor = jumlah item × 2.

**Dashboard**:
Web UI that reads ONLY from summary tables for fast performance. Default view is current week, with filter for custom periods.

**Inspector Performance**:
Metric ketiga: jumlah inspeksi APPROVED per inspector per bulan. Dihitung via query langsung ke tabel `inspections` (JOIN dengan `users`) — bukan dari summary table — karena data ini sederhana dan tidak perlu pre-computation. Endpoint: `GET /api/analytics/inspector-performance?year_month=YYYY-MM`.

**Filter Date**:
Menggunakan date-range filter (>= start_of_month, < next_month) untuk kompatibilitas cross-DB (SQLite + PostgreSQL). Tidak menggunakan `.like()` pada Date column yang hanya bekerja di SQLite.

**Two Metrics**:
1. Rooms with lowest score percentage (default: top 3)
2. Most frequently scored items (score 0)

## Key Decisions

- Dashboard SELECTs ONLY from pre-computed summary tables
- Summary tables UPSERTed by background jobs when inspection status changes to APPROVED
- Default view: current week (not month)
- Scoring formula: (actual / max) × 100%
- Analytics recalculation triggered via `background_jobs` table (outbox pattern) — lihat `backend/app/modules/background/CONTEXT.md` untuk detail implementasi
- Summary data grouped by `year_month` (format: `YYYY-MM`), dashboard filter menentukan periode tampilan
- **Inspector Performance query langsung ke `inspections`** — tidak perlu summary table karena query sederhana (COUNT + GROUP BY) dan data inspector performance tidak sering diakses (berbeda dengan lowest-rooms/top-issues yang dibutuhkan dashboard setiap load)
- **Date-range filter** digunakan sebagai ganti `.like()` untuk kompatibilitas PostgreSQL

## ADRs

See `docs/adr/` for analytics-specific decisions:
- ADR-0008: User Management & Monitoring (Inspector Performance sebagai bagian dari monitoring)
