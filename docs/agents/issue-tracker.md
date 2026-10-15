# Issue tracker: `ROADMAP.md`

`ROADMAP.md` is this repo's only tracker. Each checkbox is a ticket: one squashable branch. GitHub holds code and PRs; it holds no issues, labels or triage state.

## Mapping skill operations

When a skill names a tracker operation, do this instead:

| Skill says                              | Do                                                                                                   |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Fetch / read the relevant ticket        | Read the `ROADMAP.md` item: its checkbox line, its sub-bullets, and its section's intro              |
| List open tickets                       | Read the unchecked boxes in `ROADMAP.md`, in order; the first one is next                            |
| Create / publish a ticket               | Propose the item text and its section to the user; add it to `ROADMAP.md` once they agree            |
| Comment on a ticket / record a decision | Add a sub-bullet under the item, on the item's own branch                                            |
| Close a ticket                          | Ask the user, then tick the checkbox                                                                 |
| Apply a triage label                    | Tell the user the item's state (needs info, ready for agent, ready for human, won't do) in the report |

## Not used

- **Triage labels**: an item is either listed (to be done) or not listed; the user decides which.
- **PRs as a request surface**: no. PRs only land Roadmap items.
- **Wayfinding maps, child tickets, blockers, claims**: the Roadmap's order is the dependency order, and one session works one item.
