# Relay — Blueprint Overview

Codename **Relay** (placeholder — rename freely). A background agent that keeps
emulator save data in sync across a user's devices, with per-game merge for
shared memory-card containers and non-destructive conflict handling for
everything else.

This directory is a build spec for an autonomous coding agent (Antigravity or
similar) to execute against. It supersedes two earlier documents in this
conversation's history:

1. "Emulator Save Sync Architecture" (the original AetherSync proposal) —
   correct on the failure modes of existing tools, wrong on the mechanism.
2. The teardown response — twelve defects, each with a fix. This blueprint
   is that teardown's conclusions turned into buildable specs.

Do not re-derive the architecture from the original proposal. Build from
`01-architecture.md` in this directory.

## Core principle

**Never destroy data. Never require root. Never assume both devices are
online at once.** Every task in `05-task-backlog.md` is judged against these
three rules before anything else.

## Non-goals for v1 — explicitly out of scope

An agent picking up this backlog should NOT build any of the following
unless a later milestone explicitly asks for it:

- **No virtual filesystem (FUSE/WinFSP).** Saves are read from wherever the
  emulator already writes them. See `01-architecture.md` §Capture.
- **No peer-to-peer mesh transport.** Sync goes through a cloud store.
  LAN-local transfer is a possible future optimization, not a v1 requirement.
- **No save-state byte merging.** Save states are opaque blobs, tagged and
  gated for compatibility, never merged.
- **No mobile/iOS support.** Desktop + SteamOS only for v1.
- **No GUI application.** v1 is a CLI/daemon. A GUI conflict-picker is a
  later milestone and can be a simple local web view if one is ever built.
- **No support for every console.** v1 adapters target RetroArch cores,
  DuckStation (PS1), and PPSSPP only. PS2/GameCube container parsing is
  built and tested as a standalone library (Milestone 1) but not wired into
  a live adapter until a later milestone.

## Success criteria for Milestone 1 (the gate)

Milestone 1 is a standalone Rust library, `memcard-ps1`, that can:

1. Parse a real PS1 memory card image (128 KB) into a list of save entries,
   each tagged with its product code (e.g. `BASCUS-94163`) and name.
2. Extract any single save entry as an independent, self-contained unit.
3. Take two *different* card images that each contain saves the other
   lacks, and merge them into one card containing the union of both —
   automatically, no prompts, no data loss — as long as no single save slot
   conflicts.
4. Round-trip: a card written by this library loads correctly in a real
   emulator (DuckStation) without corruption.

**Do not proceed to Milestone 2 until Milestone 1's acceptance tests pass
against real card images.** This is the go/no-go gate discussed with the
project owner. If it fails, stop and report why rather than continuing to
build on top of it.
