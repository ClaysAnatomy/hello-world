# Task Backlog

Milestones are strictly sequential. **Do not begin Milestone N+1 work until
Milestone N's acceptance criteria are met and demonstrated** (a passing test
run, not just code that compiles). This is the single most important rule
in this document — the original AetherSync proposal failed by building five
subsystems in parallel with no validated foundation under any of them.

Within a milestone, tasks can be parallelized across agents where marked
`[parallel-ok]`; tasks marked `[sequential]` depend on a prior task in the
same milestone and must not start until it's done.

---

## Milestone 0 — Workspace scaffold `[sequential, ~1 task]`

**Goal:** a Cargo workspace that builds and runs `cargo test` with zero
tests, so every later task has a place to land.

- [ ] Create the Cargo workspace per `06-repo-layout.md`. `cargo build`
      and `cargo test` succeed with no crates yet beyond stub `lib.rs`
      files. Add `.gitignore` for `target/`.

**Acceptance:** `cargo build --workspace` and `cargo test --workspace`
both exit 0 in CI (or locally if no CI is configured yet).

---

## Milestone 1 — PS1 memory card codec (THE GATE) `[mostly sequential]`

**Goal:** see `00-overview.md` §Success criteria for Milestone 1. This is
the go/no-go checkpoint for the entire project. Do not add any other
milestone's code to the workspace until this passes.

1. `[sequential]` **Parser**: implement `parse_card(bytes: &[u8]) ->
   Result<Card>` in `crates/memcard-ps1`, per `03-container-formats.md`.
   `Card` exposes the list of directory entries and free/used block map.
   Unit tests against at least one real, non-synthetic 128KB card image
   (source one from a personal DuckStation/RetroArch install or a
   known-good test fixture — do not hand-roll a fake card as the only
   test input, real cards have quirks synthetic ones won't).

2. `[sequential, depends on 1]` **Extraction**: implement
   `extract_units(card: &Card) -> Vec<SaveUnit>`, splitting a parsed card
   into independent per-game units per the algorithm in
   `03-container-formats.md`. Test: extracting from a card with multiple
   games and at least one multi-block save yields the correct count of
   units with correct product codes.

3. `[sequential, depends on 2]` **Reassembly**: implement
   `write_card(units: &[SaveUnit]) -> Vec<u8>` (fresh card) and
   `merge_units(card: &mut Card, incoming: &[SaveUnit]) -> MergeReport`
   (existing card + additions, per the merge algorithm). `MergeReport`
   must distinguish: added silently, already-present (skipped), and
   same-slot conflict (needs escalation — do not auto-resolve).

4. `[parallel-ok, depends on 3]` **Round-trip test**: parse a real card →
   extract all units → reassemble → byte-compare to the original. Any
   byte difference is a failing test, not a warning.

5. `[parallel-ok, depends on 3]` **Merge test**: take two different real
   cards (or one card split into two synthetic-but-realistic halves) with
   no overlapping saves, merge, confirm the result contains the union and
   loads correctly. **This step should be validated by actually loading
   the resulting card image in DuckStation** — an emulator not accepting
   the file is a failure even if the byte-level logic looks correct.

6. `[parallel-ok, depends on 3]` **Conflict-detection test**: two cards
   with the same product code + save label but different bytes — confirm
   `MergeReport` reports a conflict for that unit and does NOT silently
   pick one side.

7. `[parallel-ok, depends on 1]` **Wrapped-format ingest**: implement
   stripping for at least `.gme` (3904-byte header) and confirm the
   stripped payload parses identically to a native `.mcr`/`.mcd` of the
   same card.

**Acceptance (must all pass before Milestone 2 starts):**
- Tasks 4, 5, and 6 pass as automated tests using real card data, not
  only synthetic fixtures.
- Task 5's output has been loaded in an actual emulator at least once and
  confirmed to read correctly (this can be a manually-verified step,
  documented in the PR/commit, if a real automated emulator-in-CI harness
  isn't feasible yet).
- If any of this fails or reveals the format is too irregular in practice
  to merge reliably: **stop, do not proceed to Milestone 2**, and report
  back what specifically broke. That outcome is a valid and useful result
  of this milestone, not a failure of the task.

---

## Milestone 2 — Storage backend `[parallel-ok within, after M1]`

**Goal:** the content-addressed blob store + version DAG metadata service,
runnable locally for development.

- [ ] `[parallel-ok]` `crates/relay-core`: implement the `Version` and
      `Asset` structs from `02-data-schemas.md`, plus an in-memory + SQLite
      implementation of the DAG operations (insert version, list heads for
      an asset, resolve merge). Unit tests for: linear history stays
      single-headed; two concurrent writes produce two heads; resolving
      produces one head again with both prior heads as parents; nothing is
      ever deleted from the store by these operations.
- [ ] `[parallel-ok]` Blob storage via `object_store`, configured against a
      local-filesystem backend for dev/test and documented for R2/S3 for
      later deployment. Content-addressed by BLAKE3 hash. Test: writing the
      same bytes twice is a no-op on the second write (dedup); reading
      returns exactly what was written.
- [ ] `[parallel-ok]` Chunking per the tiers in `01-architecture.md`
      §Compression: whole-blob path for small files, FastCDC + zstd path
      for large files (via the `Chunker` trait wrapper from
      `04-dependencies.md`). Test: a large file with a small localized
      change re-uploads only the changed chunks.
- [ ] `[parallel-ok]` Minimal `axum` HTTP API in front of the above:
      `POST /versions`, `GET /assets/:id/heads`, `POST /blobs` (or presigned
      upload via `object_store`), `GET /blobs/:hash`. No auth required yet
      beyond a static bearer token — real auth is a later milestone, not
      part of the gate for anything downstream.

**Acceptance:** a local integration test that pushes two divergent
versions of a synthetic asset from two "device" identities and confirms
the API reports two heads; resolving via the API collapses back to one.

---

## Milestone 3 — Agent CLI, launch-wrapper mode `[mostly sequential, after M2]`

**Goal:** the actual "effortless" experience, for one OS first (recommend
Linux — simplest process-wrapper model, and the workspace can build/test on
whatever CI environment is available without needing Windows/macOS runners
yet). Windows/macOS wrapper support is a follow-on task once this pattern
is proven, not a blocker for it.

1. `[sequential]` Config loading: read `adapters/*.toml` per the schema in
   `02-data-schemas.md`, resolve which adapter applies to a given emulator
   invocation.
2. `[sequential, depends on 1]` Capture pipeline: implement the three-signal
   quiescence capture from `01-architecture.md` §Capture using `notify` +
   `notify-debouncer-full`, plus the process-exit override (via `sysinfo`
   or, in wrapper mode, simply waiting on the child process the agent
   itself spawned) and the periodic reconciliation sweep.
3. `[sequential, depends on 2]` Wrapper mode: `relay-agent run -- <emulator
   command>` — pulls latest heads for any assets the adapter maps before
   launch, execs the emulator, waits for exit, runs a forced capture, pushes.
4. `[parallel-ok, depends on 3]` Local durable outbound queue (SQLite) so
   captures made offline are not lost and drain automatically on the next
   successful network contact.
5. `[parallel-ok, depends on 3]` Conflict picker (CLI first — a simple
   terminal prompt listing device/time/size for each head is sufficient
   for v1; do not build a GUI here) per `01-architecture.md` §Conflict
   resolution UX, including "play anyway without resolving."

**Acceptance:** on one machine, running `relay-agent run --
retroarch <rom>` twice with a simulated second "device" pushing a divergent
save in between results in the conflict picker firing on the second run,
and choosing an option launches with the correct save present.

---

## Milestone 4 — Adapters `[parallel-ok, after M3]`

- [ ] `[parallel-ok]` `adapters/retroarch.toml` — validate against a real
      RetroArch install's actual default paths on at least Linux.
- [ ] `[parallel-ok]` `adapters/duckstation.toml` — battery saves plus
      wiring the `container` save-class to `memcard-ps1` from Milestone 1.
      This is the first adapter that exercises the container merge path
      end-to-end, not just in the codec's own unit tests.
- [ ] `[parallel-ok]` `adapters/ppsspp.toml` — battery saves.

**Acceptance:** for each adapter, a real save produced by that real
emulator round-trips through capture → push → pull → restore with a
byte-identical result.

---

## Milestone 5 — Leases `[parallel-ok, after M3]`

- [ ] Lease post/heartbeat/release in the metadata service and agent, per
      `01-architecture.md` §Leases. Purely advisory — verify no code path
      anywhere treats a live lease as a launch-blocking condition.

**Acceptance:** launching the same asset from a second simulated device
while a lease is live shows the warning; launching proceeds regardless.

---

## Explicitly deferred — do not schedule unless asked

- PS2 / GameCube codecs (Milestone 1 pattern extends to them; not urgent
  until Milestone 1 is validated and there's a live adapter wanting them).
- Windows / macOS wrapper support (same pattern as Milestone 3, new OS).
- Any GUI.
- P2P/LAN-local transfer optimization.
- Multi-user / sharing features.
