.PHONY: install dev dev-pg migrate seed reset clean-db clean test
.PHONY: frontend-install frontend-dev frontend-build
.PHONY: docker-up docker-down docker-logs
.PHONY: db-up db-shell db-psql pg-migrate pg-reset all

# ── Backend (SQLite — development) ──

install:
	cd backend && uv sync

dev:
	cd backend && PYTHONPATH=. uv run fastapi dev app/main.py --port 8100

migrate:
	cd backend && PYTHONPATH=. uv run alembic upgrade head

seed:
	cd backend && uv run python -m app.seed

reset: clean-db migrate seed
	@echo "✅ Database reset complete"

clean-db:
	rm -f backend/rsud.db
	@echo "🗑️  SQLite database deleted"

# ── Backend (PostgreSQL — production-like) ──

db-up:
	docker compose up -d db
	@echo "⏳ Waiting for PostgreSQL to be healthy..."
	@sleep 3
	@docker compose exec db pg_isready -U rsud || sleep 3
	@echo "✅ PostgreSQL is ready"

db-shell:
	docker compose exec db psql -U rsud -d rsud

db-psql:
	PGPASSWORD=rsud_secret psql -h localhost -p 5433 -U rsud -d rsud

dev-pg: export DATABASE_URL=postgresql+asyncpg://rsud:rsud_secret@localhost:5433/rsud
dev-pg:
	cd backend && PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://rsud:rsud_secret@localhost:5433/rsud uv run fastapi dev app/main.py --port 8100

pg-migrate:
	cd backend && PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://rsud:rsud_secret@localhost:5433/rsud uv run alembic upgrade head

pg-seed:
	cd backend && PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://rsud:rsud_secret@localhost:5433/rsud uv run python -m app.seed

pg-reset: pg-migrate pg-seed
	@echo "✅ PostgreSQL reset complete"

# ── Migration tooling ──

migrate-to-pg:
	cd backend && PYTHONPATH=. DATABASE_URL_SRC=sqlite+aiosqlite:///./rsud.db DATABASE_URL_DST=postgresql+asyncpg://rsud:rsud_secret@localhost:5433/rsud uv run python -m scripts.migrate_to_postgresql

# ── Frontend ──

frontend-install:
	cd web-admin && npm install

frontend-dev:
	cd web-admin && npm run dev

frontend-build:
	cd web-admin && npm run build

# ── Docker (full stack) ──

docker-up:
	docker compose up --build -d

# WARNING: docker-down -v destroys ALL volumes (data loss!)
docker-down:
	docker compose down

docker-down-volumes:
	docker compose down -v

docker-logs:
	docker compose logs -f

# ── Utils ──

test:
	cd backend && PYTHONPATH=. uv run pytest tests/ -v

clean: clean-db
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .venv -exec rm -rf {} + 2>/dev/null || true
	rm -rf web-admin/dist web-admin/node_modules
	@echo "🧹 Clean complete"

all:
	@echo "Starting backend (port 8100) and frontend (port 5173)..."
	@echo "Open http://localhost:5173"
	trap 'kill 0' EXIT; \
	cd backend && PYTHONPATH=. uv run fastapi dev app/main.py --port 8100 & \
	cd web-admin && npm run dev
