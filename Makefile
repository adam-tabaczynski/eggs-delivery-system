.PHONY: psql seed lint typecheck check test migrate-local migrate-test

psql:
	docker compose exec db psql -U eggs -d doorstep_eggs

# Local db only (never db_test); idempotent, run after migrate-local.
seed:
	docker compose exec -T db psql -U eggs -d doorstep_eggs -v ON_ERROR_STOP=1 -f - < docker/seed.sql

# Fixes in place; lint before format, as in pre-commit.
lint:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run pyright

# Read-only lint + format + types; CI's lint job runs this.
check:
	uv run ruff check .
	uv run ruff format --check .
	uv run pyright

# Extra pytest args via ARGS, e.g. make test ARGS="tests/unit -k order"
test:
	uv run pytest $(ARGS)

migrate-local:
	POSTGRES_HOST=localhost POSTGRES_PORT=5432 uv run --env-file docker/db.env alembic upgrade head

migrate-test:
	POSTGRES_HOST=localhost POSTGRES_PORT=5433 uv run --env-file docker/db-test.env alembic upgrade head
