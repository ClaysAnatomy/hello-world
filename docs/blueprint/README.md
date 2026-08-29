# Blueprint index

Build spec for **Relay** (codename, placeholder), a cross-platform emulator
save-sync agent. Written for an autonomous coding agent (e.g. Antigravity)
to execute against directly.

Read in this order:

1. [`00-overview.md`](./00-overview.md) — what this is, non-goals, the
   Milestone 1 success criteria (the go/no-go gate).
2. [`01-architecture.md`](./01-architecture.md) — the corrected design:
   version DAG, capture pipeline, transport, conflict UX, leases.
3. [`02-data-schemas.md`](./02-data-schemas.md) — exact structs, the
   adapter manifest format, local + server-side tables.
4. [`03-container-formats.md`](./03-container-formats.md) — PS1/PS2/
   GameCube memory card byte layouts. Primary reference for Milestone 1.
5. [`04-dependencies.md`](./04-dependencies.md) — audited crate list
   (adopt / caution / reject) with live registry data and reasoning.
6. [`05-task-backlog.md`](./05-task-backlog.md) — the sequenced,
   milestone-gated task list. **Start here for "what do I build first."**
7. [`06-repo-layout.md`](./06-repo-layout.md) — the Cargo workspace
   structure these tasks land in.

## The one rule that matters most

Milestone 1 (`memcard-ps1`, a standalone PS1 memory-card codec) is a hard
gate. Nothing else in this backlog should be built before it passes its
acceptance tests against real card data. If it fails, that is a valid and
useful outcome — report it, don't route around it by building the rest of
the system anyway.
