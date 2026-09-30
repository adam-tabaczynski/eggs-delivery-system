---
status: accepted
---

# Lock the cycle row on every order write

FCFS capacity (allocated eggs + new quantity `<= max_eggs`) and "at most one `open` order per Customer per cycle" are both check-then-write rules. Under Postgres's default READ COMMITTED, two concurrent requests can both pass the check and both write, overbooking the cycle or creating two open orders. We serialize every write to a cycle's orders by taking `SELECT ... FOR UPDATE` on the delivery cycle row (`get_for_update`) before any check. The cycle row is the natural lock: every order write already reads it, and all rules being protected are scoped to one cycle.

## Considered options

- **SERIALIZABLE isolation**: correct, but conflicting transactions fail with a serialization error, so every write path needs retry machinery. The lock gives the same safety by waiting instead of failing.
- **Stored `allocated_eggs` counter on the cycle**: turns capacity into one atomic `UPDATE ... WHERE allocated_eggs + :q <= max_eggs`, but it's a second copy of the sum to keep in sync on every place, update and cancel, and it doesn't cover the one-open-order rule.
- **Optimistic `version` column**: detects the conflict after the fact; like SERIALIZABLE it needs retries, and the version would have to live on the cycle anyway.
- **Postgres advisory locks**: same effect as the row lock, but the lock key is an arbitrary number outside the schema; nothing ties it to the cycle row it protects.
- **In-process Python locks**: don't work across workers or processes.
- **Partial unique index for one-open-order** (`UNIQUE (cycle_id, customer_id) WHERE status = 'open'`): would cover only #13, not capacity, and the lock already covers both. Not added, so the rule lives in one place.

## Consequences

- Any new write that can change a cycle's open orders or its capacity must take the same lock first: Provider cancel cycle (cascades orders to `cancelled`) and Provider update delivery cycle (changes `max_eggs`, `cutoff_at`).
- `update_order` loads the order before taking the lock, so it must re-read the order (`session.refresh`) after the lock; otherwise it checks a stale copy (the double-click race on cancel/update).
- `FOR UPDATE` blocks rather than fails, with no timeout. A slow or stuck request holding the lock blocks every other write to that cycle. Acceptable at this scale; revisit with `SET lock_timeout` or `NOWAIT` if it becomes a problem.
- Writes to the same cycle run one at a time. That caps throughput per cycle, which is fine for a single Provider's order book.
