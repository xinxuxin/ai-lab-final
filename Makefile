PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
BLACK := $(VENV)/bin/black
MYPY := $(VENV)/bin/mypy

.PHONY: install-backend install-frontend dev-backend dev-frontend test-backend build-frontend lint format typecheck

install-backend:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e "backend[dev]"

install-frontend:
	cd frontend && npm install

dev-backend:
	cd backend && ../$(VENV)/bin/uvicorn app.main:app --reload --app-dir src --port 8000

dev-frontend:
	cd frontend && npm run dev

test-backend:
	cd backend && ../$(PYTEST)

build-frontend:
	cd frontend && npm run build

lint:
	cd backend && ../$(RUFF) check src tests

format:
	cd backend && ../$(BLACK) src tests

typecheck:
	cd backend && ../$(MYPY) src

