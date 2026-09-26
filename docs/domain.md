# Domain

The rules as they stand in the code. Update this file in the same branch that changes a rule.
`ROADMAP.md` covers what comes next; this file covers what is true now.

## Glossary

- **Provider**: the single egg seller. Seeded via `docker/seed.sql`; there is no registration API.
- **Customer**: registers via `POST /customers`. Identified by `customer_id` in the path until Auth lands.
- **Delivery cycle**: one delivery date offered by the Provider, with a `cutoff_at` for ordering and a `max_eggs` capacity.
- **Stored status** (cycle): `open` / `closed` as persisted. Only the Provider's explicit close changes it.
- **Effective status** (cycle): `closed` if stored status is `closed` **or** `now >= cutoff_at`; otherwise `open`. Every API response and every rule uses the effective status (`DeliveryCycle.effective_status`).
- **Order**: a Customer's request for `quantity` eggs in one cycle. Status is `open` or `cancelled`.
- **Allocated eggs** (`allocated_eggs`): sum of `quantity` over the cycle's `open` orders. Cancelled orders do not count. Computed on read, not stored.
- **FCFS**: first come, first served. Orders are accepted while allocated eggs plus the new quantity fit within `max_eggs`; otherwise they are rejected.

## Design decisions

- `Customer` and `Provider` are separate tables, not a shared User table with a role.
- Exactly one Provider. Nothing is scoped by tenant beyond `provider_id` on cycles.
- Until Auth lands, callers pass `provider_id` / `customer_id` in the path. This is not authorization.

## Invariants

| # | Rule | Enforced in |
|---|------|-------------|
| 1 | Provider and Customer `email` unique (exact string, case-sensitive) | DB unique constraint + `register_customer` pre-check |
| 2 | Cycle `max_eggs >= 1` | Schema (`DeliveryCycleCreate`) only |
| 3 | Cycle `delivery_at` / `cutoff_at` timezone-aware | Schema only |
| 4 | Cycle `cutoff_at < delivery_at` | Schema only |
| 5 | Closing a cycle is one-way; closing an already (effectively) closed cycle → 409 `cycle_already_closed` | `update_delivery_cycle` |
| 6 | Order `quantity >= 1` | Schema (`OrderCreate`, `OrderUpdate`) only |
| 7 | Place / update / cancel an order only while cycle is effectively `open` → else 409 `cycle_already_closed` | `place_order`, `update_order` |
| 8 | Cancel is one-way; any change to a cancelled order → 409 `order_already_cancelled` | `update_order` |
| 9 | PATCH order changes exactly one of `quantity` / `status` | Schema (`OrderUpdate`) |
| 10 | Allocated eggs + new/changed quantity `<= max_eggs` → else 409 `cycle_capacity_exceeded` | `place_order`, `update_order` (read-then-write, no lock) |
| 11 | A Customer can only see / change their own orders; someone else's order → 404 `order_not_found` | `update_order`, `list_orders_for_customer` |
| 12 | A Provider can only close their own cycles; someone else's cycle → 404 `cycle_not_found` | `update_delivery_cycle` |
| 13 | At most one `open` order per Customer per cycle; POST when one exists → 409 `open_order_already_exists` (change quantity with PATCH; the 409 has no order id, find it via `GET /customers/{id}/orders`). Cancelled orders don't count | `place_order` (read-then-write, no lock, no DB index) |

"Schema only" means the rule is checked at the HTTP boundary but not in the DB. "No lock" means two requests at the same time can both pass the check.

## Capabilities (current API)

| Who | Endpoint | Notes |
|-----|----------|-------|
| Customer | `POST /customers` | Register |
| Provider | `POST /providers/{id}/cycles` | Create cycle (stored `open`) |
| Provider | `GET /providers/{id}/cycles` | Own cycles, by `delivery_at` |
| Provider | `PATCH /providers/{id}/cycles/{cycle_id}` | Close only (`status: closed`) |
| Customer | `GET /customers/{id}/cycles` | **All** cycles (open + past), by `delivery_at` |
| Customer | `POST /customers/{id}/orders` | Place order |
| Customer | `GET /customers/{id}/orders` | Own orders (open + cancelled), by `created_at` |
| Customer | `PATCH /customers/{id}/orders/{order_id}` | Change quantity **or** cancel |

## Open questions

- **FCFS and one-open-order under concurrency** (#10, #13): two concurrent orders can both pass the capacity check and together go over `max_eggs`; two concurrent POSTs from one customer (e.g. a double-click) can both pass the one-open-order check. **Decided, to implement** (next Roadmap item):
  - Every order write (`place_order`, `update_order`) locks its cycle row with `SELECT ... FOR UPDATE` before any check. Writes to the same cycle then run one at a time.
  - `update_order` loads the order only to find its `cycle_id`, locks the cycle, then **re-reads the order** (`session.refresh` / `populate_existing=True`) before its checks. Without this, the session's cached copy could be stale.
  - This also closes the double-click race on one-open-order: the second POST waits, then sees the first order.
  - A future "Provider: update delivery cycle" (changing `max_eggs` / `cutoff_at`) must take the same lock.
  - Rejected: SERIALIZABLE (needs retry machinery), stored `allocated_eggs` counter (a second copy to keep in sync), optimistic `version` column, advisory locks, and in-process Python locks (don't work across workers).
- **Concurrent cycle close** (#5): two concurrent closes both read `open`, and both return 200 instead of the second getting 409. The close's own `UPDATE` already locks the row, so order writes stay correct. **Accepted for now**: a close has no side effects yet. Fix when one attaches (e.g. "cycle closed" emails or jobs in the Email / Background work phases) with a conditional update: `UPDATE ... SET status = 'closed' WHERE id = :id AND status = 'open' AND cutoff_at > now()`, 0 rows → 409.
- **DB-level checks** (#2, #6): add `CHECK` constraints, or keep these rules in schemas only? (See the Roadmap's optional constraints item.)
- **Cycle creation in the past**: `cutoff_at` can be earlier than now, which creates a cycle that is already effectively closed. Reject it?
- **Email case**: `A@x.com` and `a@x.com` count as different customers. Normalise? (Probably with `EmailStr` in Auth.)
- **Customer cycle list**: returns every cycle, including closed and past ones. Filtering comes later (Roadmap).
