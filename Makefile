.PHONY: install dev migrate seed reset clean-db clean test
.PHONY: frontend-install frontend-dev frontend-build
.PHONY: docker-up docker-down docker-logs all

# ── Backend ──

install:
	cd backend && uv sync

dev:
	cd backend && uv run fastapi dev app/main.py --port 8000

migrate:
	cd backend && uv run alembic upgrade head

seed:
	cd backend && uv run python -m app.seed

reset: clean-db migrate seed
	@echo "✅ Database reset complete"

clean-db:
	rm -f backend/rsud.db
	@echo "🗑️  Database deleted"

# ── Frontend ──

frontend-install:
	cd web-admin && npm install

frontend-dev:
	cd web-admin && npm run dev

frontend-build:
	cd web-admin && npm run build

# ── Docker ──

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v

docker-logs:
	docker compose logs -f

# ── Utils ──

test:
	cd backend && uv run pytest -v tests/ || echo "⚠️  No tests yet"

clean: clean-db
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .venv -exec rm -rf {} + 2>/dev/null || true
	rm -rf web-admin/dist web-admin/node_modules
	@echo "🧹 Clean complete"

all:
	@echo "Starting backend (port 8000) and frontend (port 5173)..."
	@echo "Open http://localhost:5173"
	trap 'kill 0' EXIT; \
	cd backend && uv run fastapi dev app/main.py --port 8000 & \
	cd web-admin && npm run dev
