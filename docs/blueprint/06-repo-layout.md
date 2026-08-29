# Repo Layout

Cargo workspace. Crate boundaries follow the milestone boundaries in
`05-task-backlog.md` on purpose — each crate should be independently
testable without standing up the others.

```
.
├── Cargo.toml                  # [workspace] members listed below
├── crates/
│   ├── memcard-ps1/             # Milestone 1 — the gate. Zero deps on
│   │                             #   relay-core; pure codec, no networking,
│   │                             #   no async. Easiest crate to fully test
│   │                             #   in isolation.
│   │   ├── src/lib.rs
│   │   └── tests/
│   │       └── fixtures/        # real card images used by round-trip /
│   │                             #   merge / conflict tests — see M1 tasks
│   │
│   ├── memcard-ps2/             # deferred — same shape as memcard-ps1
│   ├── memcard-gc/              # deferred — same shape as memcard-ps1
│   │
│   ├── relay-core/              # Milestone 2 — Version/Asset structs,
│   │   │                         #   DAG operations, Chunker trait wrapping
│   │   │                         #   fastcdc, storage trait over object_store.
│   │   │                         #   No CLI, no process-watching — a library.
│   │   └── src/
│   │       ├── dag.rs
│   │       ├── asset.rs
│   │       ├── chunk.rs
│   │       └── store.rs
│   │
│   ├── relay-server/            # Milestone 2 — axum HTTP API in front of
│   │   └── src/main.rs          #   relay-core, deployable standalone.
│   │
│   └── relay-agent/             # Milestone 3 — the CLI binary users
│       └── src/                 #   actually run. Depends on relay-core
│           ├── main.rs          #   (client-side) and memcard-ps1 (via
│           ├── capture.rs       #   the container save-class handler).
│           ├── adapter.rs
│           ├── wrapper.rs
│           └── picker.rs
│
├── adapters/                    # Milestone 4 — TOML manifests, not code.
│   ├── retroarch.toml
│   ├── duckstation.toml
│   └── ppsspp.toml
│
└── docs/
    └── blueprint/                # this directory
```

## Notes for whoever scaffolds Milestone 0

- `memcard-ps1` should have **no dependency on `relay-core`** and vice
  versa isn't true either way — keep the codec crate a leaf with only
  `serde` (for `SaveUnit` if it needs to serialize) and no async runtime.
  This is what makes Milestone 1 gateable in true isolation: it should be
  possible to `cargo test -p memcard-ps1` with nothing else in the
  workspace built.
- `relay-core` depends on `memcard-ps1`/`memcard-ps2`/`memcard-gc` only
  through a small trait (`ContainerCodec`) so new console codecs can be
  added without touching `relay-core` itself.
- Test fixtures (real card images) are binary data — do not commit large
  binary fixtures without checking repo size implications; a handful of
  128KB PS1 card images is trivial, but don't let this pattern extend to
  save-state-sized fixtures without deliberately deciding to (e.g. Git LFS)
  in a later milestone.
