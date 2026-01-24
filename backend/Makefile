# Makefile for backend development

.PHONY: test test-v serve migrate help

help:
	@echo "Available commands:"
	@echo "  make test      - Run tests"
	@echo "  make test-v    - Run tests (verbose)"
	@echo "  make serve     - Start dev server"
	@echo "  make migrate   - Run migrations"

test:
	PYTHONPATH=. .venv/bin/pytest

test-v:
	PYTHONPATH=. .venv/bin/pytest -v

serve:
	.venv/bin/uvicorn app.main:app --reload --port 8000

migrate:
	.venv/bin/alembic upgrade head
