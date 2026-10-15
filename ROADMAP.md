# Roadmap

Checklist for Doorstep Eggs.

Each checkbox is one squashable branch (feature, refactor, chore, or test).  
At the end of the work of each squashable branch, ask user if you can mark the checkbox.  
Work the next open item unless the user asks otherwise. Do not implement later sections ahead of the list.

## Bootstrap

- [x] Bootstrap uv Python 3.13 project
- [x] Add agent guidance
- [x] Add project README
- [x] Add git conventions to AGENTS.md
- [x] Initial `ROADMAP.md`
- [x] Flat `src/` package with config + sync SQLAlchemy setup
- [x] `GET /health`
- [x] `Dockerfile` + `docker-compose.yml` (api + PostGIS)
- [x] `.env.example` (`POSTGRES_*` parts required at runtime)
- [x] pytest smoke test for `/health`



## Identity

No auth yet (see **Auth**). No customer/provider location yet (see **Geospatial**).  
Caller passes `provider_id` / `customer_id` where needed until Auth lands.

- [x] Install `Alembic` - database migration tool
- [x] `Provider`: `id`, `name`, `email` (unique), `created_at`, `updated_at`
- [x] `Customer`: `id`, `first_name`, `last_name`, `email` (unique), `created_at`, `updated_at`
- [x] Generate migration files
- [x] Idempotent SQL seed for one Provider (`docker/seed.sql`, after migrations; no provider register API)



## Application layers

First write path; multilayer dirs so Delivery cycles and Orders stay thin.

- [x] Unit of Work pattern
- [x] `controllers/`, `commands/`, `repositories/`, `exceptions/` (flat modules by concern)
- [x] `tests/`: `unit/` / `integration/` / `functional/` (FakeUoW in unit; agent test guidance)
- [x] Customer registration endpoint



## Delivery cycles

- [x] `DeliveryCycle`: `id`, `provider_id`, `delivery_at`, `cutoff_at`, `max_eggs`, `status` (`open` / `closed`), `created_at`, `updated_at`
- [x] Provider: create cycle; list cycles by `provider_id`
- [x] Separate DB / schema for testing
- [x] Granular exceptions
- [x] Provider: explicit close; also treat as closed when `now >= cutoff_at`
- [x] Common clock class
- [x] Customer: list cycles (open + past; filtering later)



## Orders

- [x] `Order`: `id`, `cycle_id`, `customer_id`, `quantity` (≥ 1), `status` (`open` / `cancelled`), `created_at`, `updated_at`
- [x] Place / update quantity / soft-cancel only before cutoff while cycle open
- [x] Customer: list own orders (open + cancelled)
- [x] FCFS capacity: sum of open quantities ≤ `max_eggs`
- [x] Refactor tests: drop fakes, model generators, regroup files, truncate after suite
- [x] `docs/domain.md`: glossary, invariants (+ where enforced), open questions; CLAUDE.md points to it
- [x] One open order per customer per cycle; POST when one exists → 409 (use PATCH)
- [x] Lock cycle row (`SELECT ... FOR UPDATE`) on order writes: FCFS + one-open-order safe under concurrency
- [x] ADR in `docs/adr/`: cycle-row lock and rejected concurrency alternatives (moved out of `docs/domain.md` open questions)
- [x] Extract `run_concurrently` test helper (barrier/thread/lock/join boilerplate shared by the concurrency tests) to `tests/helpers.py`
- [x] CI: GitHub Actions on PRs and `main` running `ruff check`, `ruff format --check`, `pyright` and `pytest` (PostGIS service container, migrations applied)
- [x] Rework Git rules in agent guardrails (CLAUDE.md, `/ship` skill): drop long-lived phase branches
- [x] Reject cycle creation when `cutoff_at` is not in the future
- [x] Provider: list orders for a cycle (open + cancelled)
- [x] Add filtering of open / cancelled orders for Customer (own) and Provider (for a cycle)
- [x] Provider: get number of allocated_eggs / max_eggs on delivery cycle
- [x] Customer: see allocated_eggs / max_eggs on cycle list
- [x] [Optional] Consider putting constraints on no. of eggs in Orders and DeliveryCycles
- [x] Conditional cycle close (`UPDATE ... WHERE status = 'open' AND cutoff_at > now()`, 0 rows → 409): concurrent close can't overwrite a final status
- [x] Provider: cancel cycle before `delivery_at` (stored `cancelled`, open orders cascade to `cancelled`, takes cycle-row lock)
- [x] Shared `client` fixture in `tests/functional/conftest.py` instead of a `TestClient(app)` per module; say so in `.claude/rules/tests.md`
- [x] Functional happy paths assert the full response body (`json_datetime` for known datetimes, `ANY` for server-made values)
- [x] Integration command/query tests assert only rule-proving fields (e.g. `status`, `updated_at` bumped); read back the cycle-cancel cascade
- [ ] Make `ROADMAP.md` the only tracker: correct the Issue tracker section in `CLAUDE.md` and `docs/agents/issue-tracker.md`
- [ ] Record grill output: rules → `docs/domain.md`; deferred ideas → Future extensions or a new Roadmap item; item-scope decisions → sub-bullets under the Roadmap item; lasting trade-offs → ADR. Say so in `CLAUDE.md` **Domain**
- [ ] Review step before the report: Haiku `test-runner` agent runs `make check` + `make test`, then code review (`mattpocock-skills:code-review` for `feat/` with the Roadmap item as spec; built-in `/code-review` for `fix/`); findings fixed or listed in Follow-ups
- [ ] Test-list-first for state-transition and concurrency items: Claude proposes the integration test list, user reviews it, then red-green with `mattpocock-skills:tdd`
- [ ] `/next` skill: remove merged worktrees and branches, pull `main`, pick the next item and flag it if marked `[grill]`, create the worktree; `/ship` ticks the checkbox in the same commit; add `[grill]` markers to remaining items
- [ ] Refactor: cycle close takes the cycle-row lock and checks its status on the model (`ensure_closable`, plus `ensure_cancellable` for cancel); drop `close_if_open` / `refresh` so repositories only fetch and lock. `get_for_update` uses `populate_existing` so a cycle loaded before the lock is re-read; one shared alias for the PATCH status `Literal[CLOSED, CANCELLED]` (`schemas.py` + `commands/cycles.py`). ADR superseding the conditional-UPDATE close; record in `.claude/rules/src-layers.md` that state-transition rules live on the model behind the row lock, never in repository `WHERE` clauses
- [ ] Idempotent status PATCHes: same-state close / cancel (cycle) and cancel (order) → 200 with no write; only disallowed transitions → 409 (settle check order for cancelling an order in a cancelled cycle in `docs/domain.md` first)
- [ ] Refactor: class-based commands and queries
- [ ] Section grooming before Auth: `mattpocock-skills:domain-modeling` pass on `docs/domain.md`, `mattpocock-skills:codebase-design` pass, guardrail audit with `mattpocock-skills:writing-for-agents`, batch-grill the Auth items



## Auth

- [ ] Email + password auth for Provider and Customer
- [ ] Pydantic `EmailStr` (+ `email-validator`) on auth and identity payloads
- [ ] `current_provider` / `current_customer` dependencies (stop passing ids for authz)
- [ ] Customer: see own open order (quantity + id) per cycle on cycle list
- [ ] Provider: update delivery cycle



## Geospatial

- [ ] Customer sets house location (`Geography(Point, 4326)` via GeoAlchemy2); optional at registration
- [ ] Require house location to place an order (`place_order` rejects a Customer without one)
- [ ] Optional `Provider.depot_location`
- [ ] Route sheet for an effectively closed, non-cancelled cycle: open orders with each Customer's current location (else 409)
- [ ] Distances from `Provider.depot_location`
- [ ] Simple stop ordering (greedy nearest-neighbor)
- [ ] Keep sync; compute on request



## Email

SES-shaped later; local delivery first.

- [ ] `Notifier` abstraction
- [ ] Local console / Mailhog delivery
- [ ] Order confirmation + cutoff / delivery reminders (sync in-process at first)
- [ ] SES-shaped adapter for later AWS use



## Background work

SQS-shaped later; local queue first.

- [ ] Local queue (Redis or LocalStack SQS) + worker in Compose
- [ ] Jobs: cutoff reminders, provider digest, route computation
- [ ] API enqueues; worker processes



## Async

- [ ] Async FastAPI routes + SQLAlchemy (`asyncpg`)
- [ ] Async worker consumers
- [ ] Document what changed and why



## AWS deploy

- [ ] Compute (ECS/Fargate)
- [ ] RDS Postgres
- [ ] SES + SQS wired for real notifications/jobs
