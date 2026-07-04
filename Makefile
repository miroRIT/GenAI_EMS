PYTHON ?= python3

.PHONY: install lint test test-integration run docker-build up down migrate openapi terraform-fmt terraform-validate ci

install:
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check src tests

test:
	$(PYTHON) -m pytest tests/unit

test-integration:
	$(PYTHON) -m pytest -m integration tests/integration

run:
	$(PYTHON) -m uvicorn emergencypulse.main:app --reload --host 0.0.0.0 --port 8080

docker-build:
	docker build -t emergencypulse-api:local .

up:
	docker compose up --build -d

down:
	docker compose down

migrate:
	$(PYTHON) -m alembic upgrade head

openapi:
	$(PYTHON) scripts/export-openapi.py --output docs/openapi.json

terraform-fmt:
	terraform -chdir=infra fmt -recursive

terraform-validate:
	terraform -chdir=infra/envs/dev init -backend=false
	terraform -chdir=infra/envs/dev validate

ci: lint test openapi docker-build terraform-validate
