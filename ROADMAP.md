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
- [ ] FCFS capacity: sum of open quantities ≤ `max_eggs`
- [ ] One open order per customer per cycle; POST when one exists → 409 (use PATCH)
- [ ] Provider: list orders for a cycle (open + cancelled)
- [ ] Add filtering of open / cancelled orders for Customer (own) and Provider (for a cycle)
- [ ] Provider: get number of allocated_eggs / max_eggs on delivery cycle
- [ ] [Optional] Consider putting constraints on no. of eggs in Orders and DeliveryCycles



## Auth

- [ ] Email + password auth for Provider and Customer
- [ ] Pydantic `EmailStr` (+ `email-validator`) on auth and identity payloads
- [ ] `current_provider` / `current_customer` dependencies (stop passing ids for authz)
- [ ] Provider: update delivery cycle



## Geospatial

- [ ] Customer sets house location (`Geography(Point, 4326)` via GeoAlchemy2)
- [ ] Optional `Provider.depot_location`
- [ ] Cycle customers with coordinates
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
