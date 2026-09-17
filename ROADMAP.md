# Roadmap

Checklist for Doorstep Eggs. Mark items done when they land on `main`.

## Pre–Phase 0

- [x] Bootstrap uv Python 3.13 project
- [x] Add agent guidance for pre-Phase 0
- [x] Add project README
- [x] Add git conventions to AGENTS.md
- [x] Initial `ROADMAP.md`

## Phase 0 — Skeleton

Sync FastAPI app runnable locally via Docker.

- [x] Flat `src/` package with config + sync SQLAlchemy setup
- [x] `GET /health`
- [x] `Dockerfile` + `docker-compose.yml` (api + PostGIS)
- [x] `.env.example` (`POSTGRES_*` parts required at runtime)
- [x] pytest smoke test for `/health`

## Phase 1 — MVP domain (sync)

No auth yet (deferred to Phase 2). No customer/provider location yet (Phase 2).  
Caller passes `provider_id` / `customer_id` where needed.

### Identity

- [x] Install `Alembic` - database migration tool
- [x] `Provider`: `id`, `name`, `email` (unique), `created_at`, `updated_at`
- [x] `Customer`: `id`, `first_name`, `last_name`, `email` (unique), `created_at`, `updated_at`
- [x] Generate migration files
- [x] Idempotent SQL seed for one Provider (`docker/seed.sql`, after migrations; no provider register API)

### Application layers

First write path; this is where the multilayer dirs land so Delivery cycles and Orders stay thin.

- [x] Unit of Work pattern
- [x] `controllers/`, `commands/`, `repositories/`, `exceptions/` (flat modules by concern)
- [x] `tests/`: `unit/` / `integration/` / `functional/` (FakeUoW in unit; agent test guidance)
- [x] Customer registration endpoint

### Delivery cycles

- [x] `DeliveryCycle`: `id`, `provider_id`, `delivery_at`, `cutoff_at`, `max_eggs`, `status` (`open` / `closed`), `created_at`, `updated_at`
- [x] Provider: create cycle; list cycles by `provider_id`
- [x] Separate DB / schema for testing
- [x] Granular exceptions
- [x] Provider: explicit close; also treat as closed when `now >= cutoff_at`
- [x] Common clock class
- [ ] Customer: list cycles (open + past; filtering later)

### Orders

- [ ] `Order`: `id`, `cycle_id`, `customer_id`, `quantity` (≥ 1), `status` (`open` / `cancelled`), `created_at`, `updated_at`
- [ ] Place / update quantity / soft-cancel only before cutoff while cycle open
- [ ] FCFS capacity: sum of open quantities ≤ `max_eggs`
- [ ] One open order per customer per cycle; POST when one exists → 409 (use PATCH)
- [ ] Provider: list orders for a cycle (open + cancelled)
- [ ] Provider: committed open eggs vs `max_eggs` for a cycle

## Phase 2 — Auth, ops & geospatial

### Auth & cycle ops

- [ ] Email + password auth for Provider and Customer
- [ ] Pydantic `EmailStr` (+ `email-validator`) on auth and identity payloads
- [ ] `current_provider` / `current_customer` dependencies (stop passing ids for authz)
- [ ] Provider: update delivery cycle

### Geospatial

- [ ] Customer sets house location (`Geography(Point, 4326)` via GeoAlchemy2)
- [ ] Optional `Provider.depot_location`
- [ ] Cycle customers with coordinates
- [ ] Distances from `Provider.depot_location`
- [ ] Simple stop ordering (greedy nearest-neighbor)
- [ ] Keep sync; compute on request

## Phase 3 — Email (SES-shaped)

- [ ] `Notifier` abstraction
- [ ] Local console / Mailhog delivery
- [ ] Order confirmation + cutoff / delivery reminders (sync in-process at first)
- [ ] SES-shaped adapter for later AWS use

## Phase 4 — Background work (SQS-shaped)

- [ ] Local queue (Redis or LocalStack SQS) + worker in Compose
- [ ] Jobs: cutoff reminders, provider digest, route computation
- [ ] API enqueues; worker processes

## Phase 5 — Async migration

- [ ] Async FastAPI routes + SQLAlchemy (`asyncpg`)
- [ ] Async worker consumers
- [ ] Document what changed and why

## Phase 6 — AWS deploy

- [ ] Compute (ECS/Fargate)
- [ ] RDS Postgres
- [ ] SES + SQS wired for real notifications/jobs
