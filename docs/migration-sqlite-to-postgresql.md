# SQLite → PostgreSQL Migration Guide

## Prerequisites

- Docker installed (for PostgreSQL container)
- Python >= 3.12 with `uv`
- All dependencies installed: `make install` or `cd backend && uv sync`

## Quick Start (PostgreSQL)

```bash
# 1. Start PostgreSQL
make db-up

# 2. Run migrations & seed on PostgreSQL
make pg-migrate
make pg-seed

# 3. Start backend with PostgreSQL
make dev-pg
```

## Migrating Existing SQLite Data

If you already have data in SQLite and want to move it to PostgreSQL:

```bash
# 1. Start PostgreSQL
make db-up

# 2. Run the migration script
make migrate-to-pg
```

The script will:
1. Extract all data from your existing SQLite database
2. Create the schema in PostgreSQL
3. Import all data, preserving foreign key relationships
4. Reset PostgreSQL sequences so auto-increment starts at the right values

## Verify Migration

```bash
# Connect to PostgreSQL and check
make db-shell

# Run inside psql:
SELECT count(*) FROM users;
SELECT count(*) FROM rooms;
SELECT count(*) FROM inspections;
```

## Switching Back to SQLite

```bash
# Just change DATABASE_URL back or unset it
unset DATABASE_URL
make dev  # runs with SQLite
```

## Full Production Stack (Docker)

```bash
# Build and start everything
make docker-up

# This uses the PostgreSQL config from docker-compose.yml
# All services start: db → backend → frontend
```

## Troubleshooting

### Sequence errors on INSERT

If you see "duplicate key value violates unique constraint", reset sequences:

```bash
make db-shell
# Inside psql:
SELECT setval('users_id_seq', (SELECT max(id) FROM users));
SELECT setval('rooms_id_seq', (SELECT max(id) FROM rooms));
-- Repeat for all tables with SERIAL primary keys
```

### Connection refused

Make sure PostgreSQL is running:

```bash
docker compose ps
# Should show "rsud-db" as "Up" and healthy
```

### Boolean casting errors

This app uses SQLAlchemy ORM which handles boolean conversion automatically.
If running raw SQL, use `TRUE`/`FALSE` instead of `1`/`0`.
In Python: `True`/`False` (not `1`/`0`).

## Architecture Notes

- **Dev**: SQLite via `aiosqlite` (zero setup, single file `backend/rsud.db`)
- **Prod**: PostgreSQL via `asyncpg` (Docker container, persistent volume)
- **Tests**: In-memory SQLite (`sqlite+aiosqlite://`) — isolated per test run
- **ORM**: SQLAlchemy 2.0 Async — abstracts DB differences

The `DATABASE_URL` environment variable switches between databases at runtime.
No code changes needed — just change the connection string.
