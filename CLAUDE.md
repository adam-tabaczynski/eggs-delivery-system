# Doorstep Eggs

Single-provider egg delivery API: one Provider, many Customers.
Customers order eggs for a delivery cycle.
Provider opens cycles with cutoff + max egg capacity (FCFS).

## Stack
Python 3.13, uv, FastAPI **synchronous** (`def` routes), SQLAlchemy sync + psycopg + Alembic, Postgres + PostGIS (Docker), pytest + pytest-env.

Stick to this stack. Do not add dependencies or change paradigms (e.g. async) unless the user asks or `ROADMAP.md` has reached that work.

## Commands
```bash
docker compose up --build                  # api + db (5432) + db_test (5433)
uv run alembic upgrade head                # migrate local db
POSTGRES_PORT=5433 POSTGRES_DB=doorstep_eggs_test uv run alembic upgrade head  # migrate db_test (after new revision / fresh volume)
uv run pytest                              # pytest-env points at db_test
make psql                                  # psql into local db
```

## Architecture
Multilayer under `src/`, by concern (not by domain). Layer ownership rules are in `.claude/rules/src-layers.md`; test conventions are in `.claude/rules/tests.md`.

## Config & env
- Load settings via pydantic-settings (`src/settings.py`). Never hardcode environment values in app or test code.
- Settings builds the SQLAlchemy URL from `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`. There is no `DATABASE_URL`.
- Test env defaults live in `pyproject.toml` `[tool.pytest.ini_options].env`, not in conftest or tests.
- Do not commit `.env`. Keep `.env.example` in sync when keys change.
- Never seed `db_test`. Only the local `db` gets `docker/seed.sql`.

## Domain
- Separate `Customer` and `Provider` tables (no shared User + role)
- Seed one Provider; customers register (no provider registration API)
- Until Auth lands, callers pass `provider_id` / `customer_id`
- Cycles: provider create/list; customers list open cycles
- Orders only before `cutoff_at`; capacity `sum(qty) <= max_eggs` (FCFS)
- One open order per customer per cycle (update quantity instead of a second open order)
- Provider view: orders for a cycle + committed eggs vs `max_eggs`

## Scope & roadmap
- `ROADMAP.md` is the checklist; each checkbox is one squashable branch.
- Work the next open item unless the user asks otherwise. Do not implement later sections ahead of the list or invent unrequested work.
- When a branch's work is done, ask the user before ticking its checkbox.

## Git
Solo workflow: short-lived branches, then merge back.

**Commits:** imperative, succinct subject (about 50–72 chars). Body only when needed.

**Branch prefixes:** `feat/` new behavior · `fix/` bug fixes · `docs/` docs only · `chore/` tooling, deps, ignore rules, agent rules · `test/` tests only · `refactor/` no behavior change.

**Phase integration** (e.g. `feat/phase-1-mvp-domain`):
- Long-lived phase branch off `main`; merge to `main` **without** squash
- Short-lived feature branches **squash-merge** onto the phase branch

**Landing a branch:** push to `origin` and open a PR with `gh pr create` against `main` (or the phase branch when one is active). Never merge locally; the user merges on GitHub.
- PR title: same style as a commit subject
- PR body: `## Summary` (bullets on behavior/why) and `## Test plan` (checkboxes: `uv run pytest` plus manual checks)
