# Doorstep Eggs — agent notes

## What this is
Single-provider egg delivery API: one Provider, many Customers.
Customers set a house location and order eggs for a delivery cycle.
Provider opens cycles with cutoff + max egg capacity (FCFS).

## Current phase
Initial uv / Python 3.13 scaffolding is on `master` (`.gitignore`, `.python-version`, `pyproject.toml`, `uv.lock`).
**Phase 0 has not started yet** (no app package, Docker, or `/health` committed).

## Stack (locked for upcoming work)
- Python 3.13, uv, FastAPI **synchronous** (`def` routes)
- SQLAlchemy sync + psycopg
- Postgres + PostGIS (Docker)
- pytest + pytest-env (`DATABASE_URL` in `pyproject.toml` when tests arrive)
- Config: `app_name` may have a default; `database_url` must come from env

## Working style
- Flat `app/` layout when Phase 0 begins — no layers/repos/DDD yet
- Small steps; do not jump to async, SES, SQS, or AWS deploy early
- Prefer editing existing files over new abstractions

## Domain rules (when implementing)
- Separate `Customer` and `Provider` tables (no shared User + role)
- Location fields on Customer; optional depot on Provider later
- Orders only before `cutoff_at`; capacity `sum(qty) <= max_eggs`
- One open order per customer per cycle

## Next
Phase 0: FastAPI `/health`, Docker Compose (api + PostGIS), `.env.example`, README, health smoke test.
