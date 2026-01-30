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
