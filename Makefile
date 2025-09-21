.PHONY: dev seed test lint backend-test frontend-test

dev:
docker compose -f infra/docker-compose.yml up --build

seed:
poetry run python scripts/seed.py

backend-test:
cd backend && poetry run pytest

frontend-test:
cd frontend && npm test -- --runInBand

test: backend-test frontend-test

lint:
cd backend && poetry run ruff check app && poetry run mypy app
cd frontend && npm run lint
