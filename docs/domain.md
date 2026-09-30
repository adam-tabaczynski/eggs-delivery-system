# Domain

The rules as they stand in the code. Update this file in the same branch that changes a rule.
`ROADMAP.md` covers what comes next; this file covers what is true now, plus rules already decided for later items (**Planned rules**).

## Scope

Doorstep Eggs is an **order book** for a local provider. The system's job ends at a frozen order list and a route sheet for the delivery run.

- Delivery happens outside the system. There is no per-order fulfilment state (`delivered` / `not_delivered`).
- There is no money in the domain: no prices, amounts owed or payments.
- Customers place one-off orders for each cycle. There are no standing orders.

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
| 10 | Allocated eggs + new/changed quantity `<= max_eggs` → else 409 `cycle_capacity_exceeded` | `place_order`, `update_order`, both behind the cycle-row lock (#14) |
| 11 | A Customer can only see / change their own orders; someone else's order → 404 `order_not_found` | `update_order`, `list_orders_for_customer` |
| 12 | A Provider can only close their own cycles; someone else's cycle → 404 `cycle_not_found` | `update_delivery_cycle` |
| 13 | At most one `open` order per Customer per cycle; POST when one exists → 409 `open_order_already_exists` (change quantity with PATCH; the 409 has no order id, find it via `GET /customers/{id}/orders`). Cancelled orders don't count | `place_order`, behind the cycle-row lock (#14); no DB index |
| 14 | Every order write locks its cycle row (`SELECT ... FOR UPDATE`) before any check, so writes to the same cycle run one at a time; `update_order` re-reads the order (`session.refresh`) after taking the lock, since the session's copy could be stale | `place_order`, `update_order` |

"Schema only" means the rule is checked at the HTTP boundary but not in the DB.

Why #14 is a cycle-row lock, the rejected alternatives, and its blocking behaviour: [ADR 0001](adr/0001-cycle-row-lock-for-order-writes.md). "Provider: cancel cycle" and "Provider: update delivery cycle" (Planned rules, below) must take the same lock.

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

## Planned rules

Decided but not yet built. Each rule moves to **Invariants** (with where it's enforced) in the branch that implements it.

### Cycle lifecycle

- Stored status gains `cancelled`: `open → closed → cancelled` or `open → cancelled`. `closed` and `cancelled` are both final; there is no reopen.
- Effective status: `cancelled` if stored as `cancelled`; otherwise `closed` if stored as `closed` **or** `now >= cutoff_at`; otherwise `open`.
- After cutoff the order book is frozen. The only thing that changes orders after cutoff is a Provider cycle cancel. There is no per-order shortfall handling: the Provider sorts that out with customers directly.

### Provider: cancel cycle (Roadmap: Orders)

- The Provider can cancel their own cycle any time before `delivery_at`, including after cutoff.
- Cancelling moves the cycle's `open` orders to the existing `cancelled` order status. The reason is read from the cycle's status, so there's no separate `cancelled_by` field.
- Cancelling an already cancelled cycle → 409. Closing a cancelled cycle → 409. Cancelling at or after `delivery_at` → 409.
- The cancel takes the cycle-row lock (`SELECT ... FOR UPDATE`), so the cascade can't race with order writes.
- To undo a mistaken cancel, the Provider creates a new cycle.

### Provider: update delivery cycle (Roadmap: Auth)

- `cutoff_at` / `delivery_at` / `max_eggs` can be updated only while the cycle is effectively `open`. An update can never reopen a closed cycle.
- A new `cutoff_at` must be in the future and before `delivery_at`.
- `max_eggs` can't go below the allocated eggs → 409 `cycle_capacity_exceeded`.
- The update takes the cycle-row lock.

### Location and route sheet (Roadmap: Geospatial)

- One house location per Customer, always the delivery destination (no per-order address, no depot pickup).
- Location is optional at registration and required to place an order: `place_order` rejects a Customer without one.
- The route sheet covers the cycle's `open` orders and uses each Customer's **current** location when it's computed (no snapshot on the order).
- The route sheet is available only for effectively `closed`, non-cancelled cycles. Otherwise → 409.

## Open questions

- **Concurrent cycle close** (#5): two concurrent closes both read `open`, and both return 200 instead of the second getting 409. The close's own `UPDATE` already locks the row, so order writes stay correct. With `cancelled` coming, a racing close could also overwrite `cancelled` with `closed`, breaking "cancelled is final". **Decided, to implement before cancel cycle** (Roadmap) with a conditional update: `UPDATE ... SET status = 'closed' WHERE id = :id AND status = 'open' AND cutoff_at > now()`, 0 rows → 409.
- **DB-level checks** (#2, #6): add `CHECK` constraints, or keep these rules in schemas only? (See the Roadmap's optional constraints item.)
- **Cycle creation in the past**: `cutoff_at` can be earlier than now, which creates a cycle that is already effectively closed. **Decided, to implement** (Roadmap): reject creation unless `cutoff_at` is in the future, matching the planned rule for cycle updates.
- **Email case**: `A@x.com` and `a@x.com` count as different customers. Normalise? (Probably with `EmailStr` in Auth.)
- **Customer cycle list**: returns every cycle, including closed and past ones. Filtering comes later (Roadmap).

## Future extensions

Out of scope for now; recorded so today's model doesn't block them.

- **Standing orders**: a subscription that places an order automatically when a cycle opens. Deciding who gets capacity first, standing orders or one-off orders, turns FCFS into a real allocation rule.
- **Per-order fulfilment**: `delivered` / `not_delivered` on orders, and cycle states such as `out_for_delivery` / `completed`.
- **Money**: a price per egg on each cycle, amounts owed, and eventually real payments.
