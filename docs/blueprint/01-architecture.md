# Architecture

This is the corrected design. Where it differs from the original AetherSync
proposal, the reason is noted inline — an agent should not "fix" these back
toward the original.

## Components

```
+-------------------+        +----------------------+
|  relay-agent (CLI) |<------>|  Cloud rendezvous     |
|  runs on each      |        |  - object store (blobs)|
|  device             |        |  - metadata service    |
+---------+-----------+        |    (version DAG,       |
          |                    |     device registry,   |
          v                    |     leases)             |
+---------+-----------+        +----------------------+
| adapters/*.toml      |
| (path + save-class   |
|  discovery, no code) |
+----------------------+
```

- **relay-agent**: the only thing installed on a user's machine. A CLI/daemon,
  no elevated privileges required on any OS.
- **Cloud rendezvous**: an always-on service so two devices never need to be
  online simultaneously to converge. Object store for blob content
  (content-addressed, immutable), a small relational store for the version
  DAG and metadata. This replaces the original's serverless P2P mesh design
  (see Defect 1 in the teardown) — P2P is a later optimization, not the
  correctness mechanism.
- **Adapters**: declarative TOML manifests describing where an emulator
  keeps its saves and how to classify them. Replaces the original's VFS
  layer (Defect 7) — no kernel filesystem driver, no elevated install step.

## Data model — the version DAG

Every tracked save (a battery save, a save state, or a per-game unit
extracted from a memory card) is a node in an append-only DAG, not a file
that gets overwritten. See `02-data-schemas.md` for the exact struct.

- A node's `parents` field records what it was derived from. Zero parents =
  genesis. One parent = normal edit. Two parents = a resolved merge.
- A save's current state is its set of "heads" — nodes with no children.
  One head = converged. Two or more heads = a conflict is pending.
- Resolving a conflict creates a *new* node naming both heads as parents.
  The losing side is never deleted; it stays reachable in history forever.
- This is the model Git uses for commits, applied to binary blobs with a
  blob store that doesn't try to diff/delta them (see Compression below).
  It replaces the original's "CRDT" framing (Defect 3) — what the original
  actually described was multi-value keep-both, not a CRDT; the version DAG
  makes that model explicit and correct.

## Capture pipeline — how a write on disk becomes a synced version

No VFS. The agent watches real save directories with the `notify` crate
(inotify / ReadDirectoryChangesW / FSEvents — unprivileged on every OS).

A file is captured only when **all** of the following hold (Defect 6):

1. No filesystem-modify event on the path for `T_quiet` (default 2s).
2. Size and mtime are stable across two reads 500ms apart.
3. **Content hash is stable** across those same two reads. This is the
   signal that actually catches torn/in-progress writes; size alone is not
   sufficient — an emulator can hold a file at its final size while still
   writing into it.

Two things override the quiet timer:

- **Emulator process exit → immediate forced capture**, bypassing the
  timer. This is the highest-confidence moment and is what makes capture
  work for emulators (e.g. RetroArch) that hold the save file open and
  flush periodically for the entire session — a pure close-event watcher
  (what the original proposal specified) misses these saves entirely.
- **Periodic reconciliation sweep** (default every 60s): hash every tracked
  path regardless of events. Safety net for dropped OS events, mmap'd
  saves, and network filesystems. Also what makes the system robust to
  power loss — on restart, the sweep compares current hashes against last
  known state and captures anything that changed while the agent was down.

## Transport

1. Push: once a file is captured, chunk/compress it (see Compression), and
   upload any chunks the store doesn't already have (content-addressed —
   ask-before-send).
2. Pull: on emulator launch (wrapper mode) or on a lease-aware trigger, ask
   the metadata service for the current heads of this asset, fetch any
   blobs not already local, and write the resolved save state into the
   emulator's directory before the emulator starts.
3. A local durable queue (SQLite) holds captures made while offline. Drains
   on reconnect. The agent must never block a game launch on network
   availability — pull failures degrade to "play with whatever is on disk
   already," not an error dialog.

## Compression / chunking strategy — tiered by object class

Do not use zstd dictionary training on large objects (Defect 4 — dictionaries
are capped near 110KB and do nothing for a 500MB save state).

| Class | Size | Strategy |
|---|---|---|
| Battery save | < 1 MB | whole blob, zstd level 3 |
| Save state | 10–500 MB | FastCDC content-defined chunking (~1MB avg chunk), per-chunk zstd, content-addressed |
| Directory-tree save (Switch, PS3) | varies | per-file hash; upload changed files only; chunk any file over ~10MB |

Content-defined chunking is preferred over `zstd --patch-from` because it
needs no shared reference version between the two ends — which is exactly
the coordination you can't guarantee across two devices that may not have
synced in a while.

## Conflict resolution UX

No attempt to inject a divergent save into a game's internal save-slot
system (Defect 2 — not implementable; in-game slots are per-game binary
structures inside the SRAM blob, not something an emulator manifest
exposes).

Instead, conflicts surface once, at launch, in the wrapper:

- If an asset has two heads, show both: originating device name, wall-clock
  time, byte size, and — where available — a screenshot. RetroArch exposes
  a `SCREENSHOT` command over its network command interface; for saves with
  no natural screenshot, capture one of the emulator window at capture time.
- User picks one. That choice writes a new DAG node with both heads as
  parents. Nothing is deleted.
- "Play anyway without resolving" must also be an option — never block
  launch on the network or on user input being available.

**Exception: container memory cards resolve automatically, per save unit,
with no prompt**, because the container format lets you scope the conflict
to a single game instead of the whole card. See `03-container-formats.md`.
This is the actual product differentiator; build it first (Milestone 1).

## Leases — reducing conflicts, not just resolving them

Advisory only, never blocking (Defect 10):

- On emulator launch, the agent posts `{asset_id, device_id, started_at,
  ttl}` to the metadata service and heartbeats every 5 minutes.
- On a different device's launch, if a live lease exists for that asset,
  show it: "Your Steam Deck has had this open for 38 minutes (last seen 2
  minutes ago)." with "Play anyway" always available as a first-class
  button, never a hidden option.
- Released on clean exit; expires by TTL otherwise.

## Save-state compatibility gating

Tag every captured save state with: emulator name + exact version, core
name + exact core version, host ISA, and the state file's own internal
version header where the format exposes one (Defect 11 — the original
proposal checked only ISA, which is not the binding constraint; two
x86_64 machines on different core builds will still crash on each other's
states).

On arrival, if any of these mismatch the local emulator/core, the state is
still stored (archival value) but is **not** placed in the emulator's
states directory automatically. Surface it as "1 incompatible state
available — restore anyway?" in the agent's own store, never litter the
emulator's own folder with renamed files.

## What is explicitly NOT built this way

- No FUSE/WinFSP mount. See non-goals in `00-overview.md`.
- No `sudo` / elevated install step anywhere on any platform. If a task in
  the backlog seems to require one, stop and flag it — it means the task
  was scoped wrong (Defect 12).
