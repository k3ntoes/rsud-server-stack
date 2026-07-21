# Context: Analytics

## Responsibility

Provide CQRS-based aggregated data for the Web Dashboard via pre-computed summary tables.

## Language

**CQRS**:
Command Query Responsibility Segregation — write and read models are separate.

**room_monthly_stats**:
Pre-computed monthly stats per room. BUT default dashboard view is weekly, not monthly — filter selector allows changing period.

**issue_frequency_stats**:
Frequency table for items scoring 0 (Berisiko). Used to identify the most problematic items.

**Score Formula**:
`Skor% = (Jumlah Skor Didapat) / (Skor Maksimal) × 100%` where max skor = jumlah item × 2.

**Dashboard**:
Web UI that reads ONLY from summary tables for fast performance. Default view is current week, with filter for custom periods.

**Two Metrics**:
1. 3 rooms with lowest score percentage
2. Most frequently scored items (score 0)

## Key Decisions

- Dashboard SELECTs ONLY from pre-computed summary tables
- Summary tables UPSERTed by background jobs when inspection status changes to APPROVED
- Default view: current week (not month)
- Scoring formula: (actual / max) × 100%

## ADRs

See `docs/adr/` in this context directory for analytics-specific decisions.
