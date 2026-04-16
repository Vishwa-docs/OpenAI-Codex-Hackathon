.PHONY: infra api web worker worker-scan stack test static

infra:
	docker compose up -d postgres redis minio mailpit

api:
	uv run uvicorn services.api.app.main:app --reload --port 8000

web:
	npm run dev:web

worker:
	uv run uvicorn services.worker.app.main:app --reload --port 8001

worker-scan:
	uv run python -m services.worker.app.cli scan demo-systems/legacycart

stack:
	python3 scripts/dev_stack.py

test:
	npm run test:web && uv run pytest

static:
	uv run ruff check services
	uv run mypy services
	npm run lint:web
	npm run typecheck:web
