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
- **Stored status** (cycle): `open` / `closed` / `cancelled` as persisted. Only the Provider's explicit close or cancel changes it: `open → closed → cancelled` or `open → cancelled`. `closed` and `cancelled` are both final; there is no reopen (to undo a mistaken cancel, the Provider creates a new cycle).
- **Effective status** (cycle): `cancelled` if stored as `cancelled`; otherwise `closed` if stored as `closed` **or** `now >= cutoff_at`; otherwise `open`. Every API response and every rule uses the effective status (`DeliveryCycle.effective_status`).
- **Frozen order book**: after cutoff, orders don't change. The only exception is a Provider cycle cancel. There is no per-order shortfall handling: the Provider sorts that out with customers directly.
- **Order**: a Customer's request for `quantity` eggs in one cycle. Status is `open` or `cancelled`.
- **Allocated eggs** (`allocated_eggs`): sum of `quantity` over the cycle's `open` orders. Cancelled orders do not count. Computed on read, not stored. The same rule applies whatever the cycle's status: a closed cycle shows its frozen total, and a cancelled cycle shows 0 (the cancel leaves no `open` orders).
- **FCFS**: first come, first served. Orders are accepted while allocated eggs plus the new quantity fit within `max_eggs`; otherwise they are rejected.

## Design decisions

- `Customer` and `Provider` are separate tables, not a shared User table with a role.
- Exactly one Provider. Nothing is scoped by tenant beyond `provider_id` on cycles.
- Until Auth lands, callers pass `provider_id` / `customer_id` in the path. This is not authorization.

## Invariants

**Enforced in** names the method that holds the rule, not every caller; find callers by search. Name a command only while the check lives inline in it.

| # | Rule | Enforced in |
|---|------|-------------|
| 1 | Provider and Customer `email` unique (exact string, case-sensitive) | DB unique constraint + `register_customer` pre-check |
| 2 | Cycle `1 <= max_eggs <= 10_000` (business ceiling for one Provider's delivery run) → else 422 `request_validation` | Schema (`DeliveryCycleCreate`) only |
| 3 | Cycle `delivery_at` / `cutoff_at` timezone-aware | Schema only |
| 4 | Cycle `cutoff_at < delivery_at` | Schema only |
| 5 | Closing a cycle is one-way; closing an already (effectively) closed cycle → 409 `cycle_already_closed`, a cancelled one → 409 `cycle_already_cancelled`. Done as one conditional `UPDATE ... WHERE status = 'open' AND cutoff_at > now`; on 0 rows the cycle is re-read to pick the 409, so a concurrent close or cancel can't both succeed or overwrite a final status | `update_delivery_cycle` via `close_if_open` |
| 6 | Order `quantity >= 1`, any whole number of eggs (no carton multiples). No per-order cap: `max_eggs` bounds it through #10 | Schema (`OrderCreate`, `OrderUpdate`) only |
| 7 | Place / update / cancel an order only while cycle is effectively `open` → else 409 `cycle_already_closed`, or `cycle_already_cancelled` if the cycle is cancelled | `DeliveryCycle.ensure_open`, called by `place_order`, `update_order` |
| 8 | Cancel is one-way; any change to a cancelled order → 409 `order_already_cancelled` | `update_order` |
| 9 | PATCH order changes exactly one of `quantity` / `status` | Schema (`OrderUpdate`) |
| 10 | Allocated eggs + new/changed quantity `<= max_eggs` → else 409 `cycle_capacity_exceeded` | `place_order`, `update_order`, both behind the cycle-row lock (#14) |
| 11 | A Customer can only see / change their own orders; someone else's order → 404 `order_not_found` | `update_order`, `list_orders_for_customer` |
| 12 | A Provider can only close or cancel their own cycles or list their orders; someone else's cycle → 404 `cycle_not_found` | `update_delivery_cycle`, `list_orders_for_cycle` |
| 13 | At most one `open` order per Customer per cycle; POST when one exists → 409 `open_order_already_exists` (change quantity with PATCH; the 409 has no order id, find it via `GET /customers/{id}/orders`). Cancelled orders don't count | `place_order`, behind the cycle-row lock (#14); no DB index |
| 14 | Every write to a cycle's orders (order writes and the cycle cancel) locks the cycle row (`SELECT ... FOR UPDATE`) before any check, so writes to the same cycle run one at a time; a command that loaded an order before the lock re-reads it (`session.refresh`) after taking it, since the session's copy could be stale | `get_for_update` (every such write locks through it); re-read: `update_order` |
| 15 | Cycle `cutoff_at` in the future at creation (`cutoff_at > now`), so a new cycle is never already effectively closed → else 422 `cycle_cutoff_not_in_future` | `create_delivery_cycle` (checked after the Provider lookup) |
| 16 | The Provider can cancel their own cycle while `now < delivery_at`, including after cutoff or an explicit close. Already cancelled → 409 `cycle_already_cancelled` (checked first); at or after `delivery_at` → 409 `cycle_delivery_passed` | `update_delivery_cycle` (`status: cancelled`) |
| 17 | Cancelling a cycle moves all its `open` orders to `cancelled` (bumping their `updated_at`) in the same transaction, behind the cycle-row lock (#14), so no order write can slip an `open` order into a cancelled cycle. There is no `cancelled_by` field: in a cancelled cycle, an order cancelled by the cascade looks the same as one its Customer cancelled earlier | `update_delivery_cycle` via `cancel_open_by_cycle_id` |

"Schema only" means the rule is checked at the HTTP boundary but not in the DB. This is deliberate: the API is the only write path, so there are no `CHECK` constraints for #2 / #6.

Why #14 is a cycle-row lock, the rejected alternatives, and its blocking behaviour: [ADR 0001](adr/0001-cycle-row-lock-for-order-writes.md). The cycle cancel (#17) takes the same lock; "Provider: update delivery cycle" (Planned rules, below) must too.

## Capabilities (current API)

| Who | Endpoint | Notes |
|-----|----------|-------|
| Customer | `POST /customers` | Register |
| Provider | `POST /providers/{id}/cycles` | Create cycle (stored `open`); `allocated_eggs` is 0 |
| Provider | `GET /providers/{id}/cycles` | Own cycles, by `delivery_at`, each with `allocated_eggs` |
| Provider | `PATCH /providers/{id}/cycles/{cycle_id}` | Close (`status: closed`) or cancel (`status: cancelled`); response is the cycle with `allocated_eggs`. Customers aren't notified of a cancel yet (Roadmap: Email) |
| Provider | `GET /providers/{id}/cycles/{cycle_id}/orders` | The cycle's orders (open + cancelled), by `created_at`; any cycle status; optional `?status=` filter |
| Customer | `GET /customers/{id}/cycles` | **All** cycles (open + past), by `delivery_at`, each with `allocated_eggs` |
| Customer | `POST /customers/{id}/orders` | Place order |
| Customer | `GET /customers/{id}/orders` | Own orders (open + cancelled), by `created_at`; optional `?status=` filter |
| Customer | `PATCH /customers/{id}/orders/{order_id}` | Change quantity **or** cancel |

**Allocated eggs on cycles**: every cycle response carries `allocated_eggs` (`DeliveryCycleRead`): the Provider's create, list and close, and the Customer's cycle list. Customers see the same total as the Provider, for every cycle status (a closed cycle shows its frozen total). The client works out remaining capacity as `max_eggs - allocated_eggs`; there is no `remaining_eggs` field. The read takes no lock: it reflects the last committed order write. The Customer's cycle list doesn't show the Customer's own order (quantity or id) per cycle; they find it via `GET /customers/{id}/orders` (Roadmap: Auth).

**Order list filter** (both order lists): optional `status` query param, one value, `open` or `cancelled`. Omitted → all orders. Any other value → 422 `request_validation`. The filter uses the order's stored status only; it doesn't look at the cycle's status.

## Planned rules

Decided but not yet built. Each rule moves to **Invariants** (with where it's enforced) in the branch that implements it.

### Provider: update delivery cycle (Roadmap: Auth)

- `cutoff_at` / `delivery_at` / `max_eggs` can be updated only while the cycle is effectively `open`. An update can never reopen a closed cycle.
- A new `cutoff_at` must be in the future → 422 `cycle_cutoff_not_in_future` (`CycleCutoffNotInFuture`, the same check as invariant #15, in the command with `Clock`).
- `cutoff_at < delivery_at` must hold for the cycle after the update, comparing each field in the body against the stored value of the other. The schema can't do this for a partial body, so it lives in the command → 422 (error code to be decided when the item is built).
- `max_eggs` keeps the creation bounds (#2) and can't go below the allocated eggs → 409 `cycle_capacity_exceeded`.
- The update takes the cycle-row lock.

### Location and route sheet (Roadmap: Geospatial)

- One house location per Customer, always the delivery destination (no per-order address, no depot pickup).
- Location is optional at registration and required to place an order: `place_order` rejects a Customer without one.
- The route sheet covers the cycle's `open` orders and uses each Customer's **current** location when it's computed (no snapshot on the order).
- The route sheet is available only for effectively `closed`, non-cancelled cycles. Otherwise → 409.

## Open questions

- **Email case**: `A@x.com` and `a@x.com` count as different customers. Normalise? (Probably with `EmailStr` in Auth.)
- **Customer cycle list**: returns every cycle, including closed and past ones. Filtering comes later (Roadmap).

## Future extensions

Out of scope for now; recorded so today's model doesn't block them.

- **Standing orders**: a subscription that places an order automatically when a cycle opens. Deciding who gets capacity first, standing orders or one-off orders, turns FCFS into a real allocation rule.
- **Per-order fulfilment**: `delivered` / `not_delivered` on orders, and cycle states such as `out_for_delivery` / `completed`.
- **Accepted orders**: a cycle status meaning "closed, and the Provider has accepted the orders", so Customers know their order will be delivered. Today an effectively closed cycle only means ordering has stopped.
- **Cancel summary**: the cycle cancel response could report the orders it cancelled (a count, or the list). Today the Provider lists them with `GET …/orders?status=cancelled`, which also includes orders Customers cancelled earlier. Likely needed once Email notifies Customers of a cancel.
- **Money**: a price per egg on each cycle, amounts owed, and eventually real payments.
