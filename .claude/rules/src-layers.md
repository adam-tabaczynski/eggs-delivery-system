---
paths:
  - "src/**/*.py"
---

# src/ layer ownership

All application source lives under `src/`.

## Roles

- `controllers/` — thin FastAPI routes; HTTP error envelope in `controllers/integrations/fast_api/`; call commands/queries only; no Session
- `commands/` — write use-cases; may own business rules
- `queries/` — read use-cases; may own business rules
- `repositories/` — Session + model access only (get/save/aggregate); no policy
- `exceptions/` — leaf business-rule errors (`exceptions/rules.py`)
- `core/` — interfaces + integrations (e.g. SQLAlchemy engine/Base/UoW); `Clock` at `core/clock.py`; exception bases and buckets in `core/exceptions/`; settings stay at `src/settings.py`
- `models.py` / `schemas.py` — mapped classes and HTTP DTOs inside `src/` (split to packages later if needed)

## Repository method names

- Verb first (`get_`, `list_by_`, `sum_`, `add`), and name whose data is read even when a parameter already says it: `get_open_order_for_customer(...)`
- Existence checks return `Model | None`; the command tests `is not None` and owns the rule

## Shape

- Flat modules by concern (e.g. `commands/orders.py`); no per-domain packages
- No extra `services/` layer on top of commands/queries

## Examples

```python
# BAD — Session in a controller
def create_order(session: Session, ...):
    session.add(...)

# GOOD — controller calls a command
def create_order(...):
    return place_order(...)
```

```python
# BAD — capacity policy inside a repository
def add_order(...):
    if total + qty > max_eggs:
        raise ...

# GOOD — repository aggregates; command/query enforces policy
committed = repo.sum_quantity(cycle_id)
# use-case compares committed + qty to max_eggs
```
