# Domain Docs

How the engineering skills should consume this repo's domain documentation.

## Before exploring, read these

- **`docs/domain.md`**: the glossary, design decisions, invariants and open questions. It is the source of truth for domain rules; this repo does not use `CONTEXT.md`.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in.

If `docs/adr/` doesn't exist, proceed silently. `/domain-modeling` creates it when a decision actually gets recorded. Anything a skill would write to `CONTEXT.md` (glossary terms, resolved language) goes into `docs/domain.md` instead.

## File structure

```
/
├── docs/
│   ├── domain.md       ← glossary + rules (CONTEXT.md equivalent)
│   └── adr/            ← created lazily
└── src/
```

## Use the glossary's vocabulary

When your output names a domain concept (issue title, refactor proposal, hypothesis, test name), use the term as defined in `docs/domain.md` (e.g. *delivery cycle*, *effective status*, *allocated eggs*). Don't drift to synonyms.

If a concept isn't in the glossary yet, either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, say so explicitly rather than silently overriding:

> _Contradicts ADR-0007 (…), but worth reopening because…_
