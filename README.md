# Doorstep Eggs

Single-provider egg delivery portal: customers order eggs for scheduled doorstep delivery cycles.

## Stack

- Python 3.13
- FastAPI (synchronous)
- uv
- Postgres + PostGIS (via Docker)
- SQLAlchemy (sync) + psycopg + Alembic
- pytest

## Quick start

Copy env defaults:

```bash
cp .env.example .env
```

Run API + PostGIS:

```bash
docker compose up --build
```

Schema and seed are not applied on container start. After Postgres is up, apply migrations when you choose, then seed one Provider (`provider@doorstep-eggs.local`). There is no provider registration API.

```bash
uv run alembic upgrade head
docker compose exec -T db psql -U eggs -d doorstep_eggs -v ON_ERROR_STOP=1 -f - < docker/seed.sql
```

The insert is idempotent (`ON CONFLICT (email) DO NOTHING`). User and database names match `.env.example`.

Health check:

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

## Local development (without Docker for the API)

Requires Postgres/PostGIS reachable at `DATABASE_URL` from `.env`.

```bash
uv sync
uv run uvicorn src.main:app --reload
```

## Tests

```bash
uv run pytest
```
