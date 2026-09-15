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

Copy env defaults for host processes (uvicorn / Alembic against `db`):

```bash
cp .env.example .env
```

Run API + PostGIS (`db` on 5432, `db_test` on 5433). Compose includes `docker/compose.*.yml`. Postgres services load `docker/db.env` / `docker/db-test.env`. The API container loads `.env` and sets `POSTGRES_HOST=db`.

```bash
docker compose up --build
```

`db` publishes 5432, `db_test` publishes 5433. Schema and seed are not applied on container start. After Postgres is up, apply migrations when you choose, then seed one Provider (`provider@doorstep-eggs.local`) on the **local** database. There is no provider registration API. Do not seed `db_test`.

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

Requires Postgres/PostGIS reachable using the five `POSTGRES_*` vars from `.env` (`HOST`, `PORT`, `USER`, `PASSWORD`, `DB`). Settings assembles the SQLAlchemy URL.

```bash
uv sync
uv run uvicorn src.main:app --reload
```

## Tests

Integration and functional tests use the `db_test` Compose service (host port 5433, database `doorstep_eggs_test` from `docker/db-test.env`). pytest-env in `pyproject.toml` supplies the same five `POSTGRES_*` names for the test process. After a fresh `db_test` volume, or after a new Alembic revision, migrate the test database (user/password/host still come from `.env`):

```bash
POSTGRES_PORT=5433 POSTGRES_DB=doorstep_eggs_test uv run alembic upgrade head
uv run pytest
```
