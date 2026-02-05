# Structura Ludis - Development Makefile
# Usage: make <target>

.PHONY: help up down restart logs build clean test frontend-restart backend-restart db-reset

# Default target
help:
	@echo "Structura Ludis - Available commands:"
	@echo ""
	@echo "  Docker:"
	@echo "    make up              - Start all containers"
	@echo "    make down            - Stop all containers (preserves data)"
	@echo "    make restart         - Restart all containers"
	@echo "    make logs            - Follow all container logs"
	@echo "    make build           - Rebuild all containers"
	@echo "    make clean           - Stop containers and remove volumes (WARNING: deletes DB data)"
	@echo ""
	@echo "  Frontend:"
	@echo "    make frontend-restart  - Restart frontend with clean cache"
	@echo "    make frontend-logs     - Follow frontend logs"
	@echo "    make frontend-build    - Run frontend build check"
	@echo ""
	@echo "  Backend:"
	@echo "    make backend-restart - Restart backend container"
	@echo "    make backend-logs    - Follow backend logs"
	@echo "    make backend-shell   - Open shell in backend container"
	@echo ""
	@echo "  Database:"
	@echo "    make db-migrate      - Run database migrations"
	@echo "    make db-seed         - Load fixtures (keeps existing data)"
	@echo "    make db-fixtures     - Reset DB and load fresh fixtures"
	@echo "    make db-reset        - Reset database (WARNING: deletes all data)"
	@echo "    make db-shell        - Open psql shell"
	@echo ""
	@echo "  GROG Import (#55):"
	@echo "    make import-grog            - Import games from fixtures to DB"
	@echo "    make import-grog-force      - Re-import and update existing games"
	@echo "    make import-grog-dry        - Dry run (show what would be imported)"
	@echo "    make import-grog-live       - Import live from GROG (~2 min)"
	@echo "    make import-grog-live-force - Live import + update existing"
	@echo "    make import-grog-full       - Import ALL games from GROG (~15-20 min)"
	@echo "    make grog-list              - List curated game slugs"
	@echo "    make grog-add SLUG=x        - Add a game and regenerate fixtures"
	@echo "    make generate-grog-fixtures - Regenerate fixtures from GROG"
	@echo ""
	@echo "  Tests:"
	@echo "    make test            - Run all tests"
	@echo "    make test-backend    - Run backend tests"
	@echo "    make test-frontend   - Run frontend tests"

# =============================================================================
# Docker commands
# =============================================================================

up:
	docker compose up -d

down:
	docker compose stop

restart: down up

logs:
	docker compose logs -f

build:
	docker compose build

clean:
	@echo "WARNING: This will delete all data including the database!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose down -v

# =============================================================================
# Frontend commands
# =============================================================================

frontend-restart:
	@echo "Restarting frontend with clean cache..."
	docker compose stop sl-frontend
	docker compose rm -f sl-frontend
	docker compose up -d sl-frontend
	@echo "Frontend restarted. Waiting for it to be ready..."
	@sleep 3
	docker compose logs --tail=20 sl-frontend

frontend-logs:
	docker compose logs -f sl-frontend

frontend-build:
	cd frontend && npm run build

frontend-shell:
	docker compose exec sl-frontend sh

# =============================================================================
# Backend commands
# =============================================================================

backend-restart:
	docker compose restart sl-api

backend-logs:
	docker compose logs -f sl-api

backend-shell:
	docker compose exec sl-api bash

# =============================================================================
# Database commands
# =============================================================================

db-migrate:
	docker compose exec sl-api alembic upgrade head

db-seed:
	@echo "Loading fixtures (use db-fixtures to reset and reload)..."
	docker compose exec sl-api python -m scripts.seed_db

db-fixtures:
	@echo "WARNING: This will reset the database and load fresh fixtures!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "Stopping backend..."
	docker compose stop sl-api
	@echo "Dropping and recreating database..."
	docker compose exec sl-db psql -U sl_admin -d postgres -c "DROP DATABASE IF EXISTS structura_ludis;"
	docker compose exec sl-db psql -U sl_admin -d postgres -c "CREATE DATABASE structura_ludis;"
	@echo "Starting backend..."
	docker compose start sl-api
	@sleep 3
	@echo "Running migrations..."
	docker compose exec sl-api alembic upgrade head
	@echo "Loading fixtures..."
	docker compose exec sl-api python -m scripts.seed_db
	@echo ""
	@echo "Done! Test accounts (password: password123):"
	@echo "  Admin:     admin@structura-ludis.dev"
	@echo "  Organizer: organizer@fdj-lyon.com"
	@echo "  GM:        gm1@example.com"
	@echo "  Player:    player1@example.com"

db-reset:
	@echo "WARNING: This will delete all database data!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "Stopping backend..."
	docker compose stop sl-api
	@echo "Dropping and recreating database..."
	docker compose exec sl-db psql -U sl_admin -d postgres -c "DROP DATABASE IF EXISTS structura_ludis;"
	docker compose exec sl-db psql -U sl_admin -d postgres -c "CREATE DATABASE structura_ludis;"
	@echo "Starting backend..."
	docker compose start sl-api
	@sleep 3
	@echo "Running migrations..."
	$(MAKE) db-migrate

db-shell:
	docker compose exec sl-db psql -U sl_admin -d structura_ludis

# =============================================================================
# GROG Import commands (#55)
# =============================================================================

# Import games from fixtures to database (fast, uses pre-generated JSON)
import-grog:
	docker compose exec sl-api python -m app.cli.import_grog --from-fixtures

import-grog-force:
	docker compose exec sl-api python -m app.cli.import_grog --from-fixtures --force

import-grog-dry:
	docker compose exec sl-api python -m app.cli.import_grog --from-fixtures --dry-run

# Import games live from GROG website
# Usage:
#   make import-grog-live                    # From curated list (~2 min)
#   make import-grog-live OPTS="--full"      # All games (~15-20 min)
#   make import-grog-live OPTS="--full --letter=a"  # Only letter A
#   make import-grog-live OPTS="--full --limit=50"  # First 50 games
import-grog-live:
	docker compose exec sl-api python -m app.cli.import_grog --from-curated $(OPTS)

import-grog-live-force:
	docker compose exec sl-api python -m app.cli.import_grog --from-curated --force $(OPTS)

import-grog-live-dry:
	docker compose exec sl-api python -m app.cli.import_grog --from-curated --dry-run $(OPTS)

# Import ALL games from GROG (full scan, ~15-20 min)
import-grog-full:
	docker compose exec sl-api python -m app.cli.import_grog --full $(OPTS)

import-grog-full-dry:
	docker compose exec sl-api python -m app.cli.import_grog --full --dry-run $(OPTS)

# Fixtures generation (runs locally, fetches from GROG website)
grog-list:
	cd backend && PYTHONPATH=. poetry run python scripts/generate_grog_fixtures.py --list

grog-add:
	@test -n "$(SLUG)" || (echo "Usage: make grog-add SLUG=game-slug" && exit 1)
	cd backend && PYTHONPATH=. poetry run python scripts/generate_grog_fixtures.py --add $(SLUG)

generate-grog-fixtures:
	@echo "Fetching game details from GROG (takes ~2 minutes for 100 games)..."
	cd backend && PYTHONPATH=. poetry run python scripts/generate_grog_fixtures.py

# =============================================================================
# Test commands
# =============================================================================

test: test-backend test-frontend

test-backend:
	cd backend && PYTHONPATH=. pytest -v

test-frontend:
	cd frontend && npm test

# =============================================================================
# Development shortcuts
# =============================================================================

# Install dependencies locally (for IDE support)
install:
	cd frontend && npm install
	cd backend && pip install -e ".[dev]"

# Format code
format:
	cd backend && black . && isort .
	cd frontend && npm run lint -- --fix

# Type check
typecheck:
	cd frontend && npm run build
	cd backend && mypy app
