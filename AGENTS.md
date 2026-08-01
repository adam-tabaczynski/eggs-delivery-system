# Doorstep Eggs — agent notes

## What this is
Single-provider egg delivery API: one Provider, many Customers.
Customers set a house location and order eggs for a delivery cycle.
Provider opens cycles with cutoff + max egg capacity (FCFS).

## Current phase
**Phase 0** — sync FastAPI skeleton (`GET /health`), Docker Compose (api + PostGIS), `.env.example`, health smoke test.
Pre–Phase 0 scaffolding and docs are on `main`; Phase 0 lands via `feat/phase-0-scaffold`.

## Stack
- Python 3.13, uv, FastAPI **synchronous** (`def` routes)
- SQLAlchemy sync + psycopg
- Postgres + PostGIS (Docker)
- pytest + pytest-env (`DATABASE_URL` in `pyproject.toml`)
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

## Git conventions
Solo workflow: short-lived branches off `main`, then merge back.

**Commits:** imperative, succinct subject (about 50–72 chars). Body only when needed.

**Branch prefixes:**

| Prefix | Use for |
|--------|---------|
| `feat/` | New behavior |
| `fix/` | Bug fixes |
| `docs/` | Docs only (README, AGENTS, comments) |
| `chore/` | Tooling, deps, ignore rules, agent rules with no product change |
| `test/` | Tests only |
| `refactor/` | Restructure with no behavior change |

Examples: `feat/phase-0-scaffold`, `fix/health-response`, `chore/pytest-env`.

## Next
Merge Phase 0 to `main`, then Phase 1: Provider/Customer, cycles, orders (sync MVP domain).
