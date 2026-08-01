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

- [x] Flat `app/` package with config + sync SQLAlchemy setup
- [x] `GET /health`
- [x] `Dockerfile` + `docker-compose.yml` (api + PostGIS)
- [x] `.env.example` (`DATABASE_URL` required at runtime)
- [x] pytest smoke test for `/health`

## Phase 1 — MVP domain (sync)

- [ ] `Provider` (seeded) and `Customer` registration (location on Customer)
- [ ] Customer location as PostGIS `Geography(Point, 4326)` via GeoAlchemy2
- [ ] Delivery cycles: create/list (provider); list open cycles (customer)
- [ ] Orders: place/update/cancel before cutoff with FCFS capacity checks
- [ ] One open order per customer per cycle
- [ ] Provider view: cycle orders + committed eggs vs `max_eggs`

## Phase 2 — Geospatial value

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
