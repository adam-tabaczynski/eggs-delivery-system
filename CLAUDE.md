# Doorstep Eggs

Single-provider egg delivery API: one Provider, many Customers.
Customers order eggs for a delivery cycle.
Provider opens cycles with cutoff + max egg capacity (FCFS).

## Stack
Python 3.13, uv, FastAPI **synchronous** (`def` routes), SQLAlchemy sync + psycopg + Alembic, Postgres + PostGIS (Docker), pytest + pytest-env, ruff (lint + format via pre-commit) + pyright.

Stick to this stack. Do not add dependencies or change paradigms (e.g. async) unless the user asks or `ROADMAP.md` has reached that work.

## Commands
```bash
docker compose up --build                  # api + db (5432) + db_test (5433)
uv run alembic upgrade head                # migrate local db
POSTGRES_PORT=5433 POSTGRES_DB=doorstep_eggs_test uv run alembic upgrade head  # migrate db_test (after new revision / fresh volume)
uv run pytest                              # pytest-env points at db_test
make psql                                  # psql into local db
uv run ruff check --fix . && uv run ruff format .  # also run as pre-commit hooks; if they rewrite files, re-stage and commit again
uv run pyright                             # type check
```

**Worktrees:** never run `docker compose` from a worktree. Containers are shared: one `db` (5432) and one `db_test` (5433), started by the user from the main checkout. If `db_test` is unreachable, ask the user to start it instead of spawning another. One session runs `uv run pytest` at a time (tests truncate tables).

## Architecture
Multilayer under `src/`, by concern (not by domain). Layer ownership rules are in `.claude/rules/src-layers.md`; test conventions are in `.claude/rules/tests.md`.

## Config & env
- Load settings via pydantic-settings (`src/settings.py`). Never hardcode environment values in app or test code.
- Settings builds the SQLAlchemy URL from `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`. There is no `DATABASE_URL`.
- Test env defaults live in `pyproject.toml` `[tool.pytest.ini_options].env`, not in conftest or tests.
- Do not commit `.env`. Keep `.env.example` in sync when keys change.
- Never seed `db_test`. Only the local `db` gets `docker/seed.sql`.

## Domain
Rules, glossary and open questions live in `docs/domain.md`; it is the source of truth.
Before starting a Roadmap item, list the rule questions it raises, settle them, and record the answers in `docs/domain.md` in the same branch.

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

**Bulk reformat branches** (whole-project `ruff format`, or `ruff check --fix` sweeps, no behavior change): keep them free of other changes. After the user merges, add the squash commit's full hash to `.git-blame-ignore-revs` on a small `chore/` branch.

**One worktree per branch:** create each branch in its own worktree under `.claude/worktrees/`, named after the branch (`/` → `-`, e.g. `chore-ignore-worktrees`). Never reuse a worktree for a new branch.

**Review before commit:** when the work is done, leave changes uncommitted and stop. Report the worktree path (so the user can open it in VSCode), `git diff --stat`, and the proposed commit(s): subject, body, files in each, and order. Commit, push, and open the PR only after the user confirms. This overrides any default to commit without asking. If the user asks for edits, apply them and propose again.

The report ends with **Follow-ups**: issues noticed but not addressed by the diff (failed or skipped checks, rule gaps, nearby smells, repo hygiene, missing tests), one line each tagged `same branch`, `new branch`, `ROADMAP`, `domain`, or `env`, with where and a suggested action. Write `Follow-ups: none` if nothing came up. Never act on a follow-up without the user's go-ahead.

**Landing a branch:** once confirmed, push to `origin` and open a PR with `gh pr create` against `main` (or the phase branch when one is active). Never merge locally; the user merges on GitHub.
- PR title: same style as a commit subject
- PR body: `## Summary` (bullets on behavior/why) and `## Test plan` (checkboxes: `uv run pytest` plus manual checks)

## Agent skills

### Issue tracker

GitHub Issues on `adam-tabaczynski/eggs-delivery-system`, via `gh`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: glossary and rules in `docs/domain.md`, ADRs in `docs/adr/`. See `docs/agents/domain.md`.
