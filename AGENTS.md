# Doorstep Eggs — agent notes

## What this is
Single-provider egg delivery API: one Provider, many Customers.
Customers order eggs for a delivery cycle.
Provider opens cycles with cutoff + max egg capacity (FCFS).

## Stack
- Python 3.13, uv, FastAPI **synchronous** (`def` routes)
- SQLAlchemy sync + psycopg + Alembic
- Postgres + PostGIS (Docker)
- pytest + pytest-env

## Architecture
Target multilayer under `src/` — by concern, not by domain (dirs appear as Phase 1 lands):

```
src/
  main.py            # app factory / router wiring only
  controllers/       # thin FastAPI routes
  commands/          # write use-cases
  queries/           # read use-cases
  repositories/      # Session + model access
  exceptions/        # domain / business-rule errors
  core/              # interfaces + integrations (e.g. SQLAlchemy UoW); settings at src/settings.py
  models.py          # SQLAlchemy mapped classes
  schemas.py         # Pydantic request/response DTOs
```

## Tests

```
tests/
  unit/          # command policy with FakeUoW / FakeRepo (no Postgres)
  integration/   # real UoW, repositories, DB-backed command paths
  functional/    # HTTP via TestClient
  conftest.py
  helpers.py
```

## Domain
- Separate `Customer` and `Provider` tables (no shared User + role)
- Seed one Provider; customers register
- Cycles: provider create/list; customers list open cycles
- Orders only before `cutoff_at`; capacity `sum(qty) <= max_eggs` (FCFS)
- One open order per customer per cycle (update quantity instead of a second open order)
- Provider view: orders for a cycle + committed eggs vs `max_eggs`

## Git
Solo workflow: short-lived branches, then merge back.

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

**Phase integration** (e.g. `feat/phase-1-mvp-domain`):
- Long-lived phase branch off `main`; merge to `main` **without** squash
- Short-lived feature branches **squash-merge** onto the phase branch

Examples: `feat/phase-1-mvp-domain`, `fix/order-capacity`, `chore/pytest-env`.

## Pointers
- [ROADMAP.md](ROADMAP.md) — phases and checklist
- [README.md](README.md) — run locally
- [.cursor/rules/](.cursor/rules/) — coding constraints
