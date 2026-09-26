---
paths:
  - "tests/**/*.py"
---

# tests/ conventions

## Buckets

- `unit/` — pure functions, model methods, and custom schema validators (`field_validator` / `model_validator` in `schemas.py`); no DB, no fakes, no mocks of UoW / Session; do not test declarative Pydantic constraints (`Field(ge=...)`, `min_length`, `Literal`, `extra="forbid"`)
- `integration/commands/`, `integration/queries/` — one module + one class per command/query (`class TestPlaceOrder:`); business rules are tested here only
- `integration/repositories/`, `integration/test_uow.py` — persistence: constraints, aggregates, commit/rollback
- `functional/` — `TestClient`; one directory per resource (`customers/`, `cycles/`, `orders/`, grouped like `controllers/`), one module + one class per endpoint; JSON only, no Session
  - Happy path: one per argument mapping (e.g. update order: quantity, soft cancel)
  - One domain error: prefer the 404 for the path resource; otherwise the endpoint's own error (e.g. duplicate email 409)
  - One 422 if the endpoint takes a body
  - Other rule errors belong in `integration/`, not here

## Setup

- Build rows with `tests/generators.py` (`make_*`); never call commands for setup, never add ad-hoc `_add_*` helpers
- Generators take foreign keys as required args; create parents explicitly and pass their ids
- Assign each generated parent to its own variable (`customer`, `other_customer`); do not nest calls like `customer_id=make_customer().id`
- Generator defaults: constants in the signature; `X | None = None` only for per-call values (uuid email, times relative to now)
- Each test method builds its own rows; never share state through `self` or class-scoped fixtures
- Time: real `Clock()` + `move_datetime_forward` / `backward`

## Assertions

- Command/query tests assert the returned DTO against inputs and generated rows; do not read back through a new UoW
- Failure cases assert only the leaf error (`CycleNotFound`, `CycleCapacityExceeded`)
- Only `repositories/` and `test_uow.py` read back via UoW; they assert `NotFoundError` / `ConflictError`
- Queries that read across all rows (e.g. `list_cycles_for_customer`) assert only on rows the test created; earlier methods in the class leave rows behind
- Never assert literal ids

## DB cleanup

- Integration: autouse class-scoped truncate; functional: module-scoped; unit: none
- Truncate only through `truncate_tables()` (refuses non-`_test` databases); never seed `db_test`
