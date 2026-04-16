.PHONY: infra api web worker worker-scan stack test

infra:
	docker compose up -d postgres redis minio

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
