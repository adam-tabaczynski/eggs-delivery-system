# Doorstep Eggs

Single-provider egg delivery portal: customers order eggs for scheduled doorstep delivery cycles.

## Stack

- Python 3.13
- FastAPI (synchronous)
- uv
- Postgres + PostGIS (via Docker)
- SQLAlchemy (sync) + psycopg
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

Health check:

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

## Local development (without Docker for the API)

Requires Postgres/PostGIS reachable at `DATABASE_URL` from `.env`.

```bash
uv sync
uv run uvicorn app.main:app --reload
```

## Tests

```bash
uv run pytest
```
