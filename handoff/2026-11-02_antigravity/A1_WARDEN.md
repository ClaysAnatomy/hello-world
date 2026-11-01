# Agent 1: Warden (Phases A and D)

Paste this whole file as the first message to a new Antigravity agent whose workspace is the project folder on D:.

## Goal
Make the project safe to build on, then bring the two build lanes together and hand over. You own everything irreversible: backups, tags, branches, worktrees, merges, and the one report Aetherius reads. You write no feature code.

## Read first, in order
1. `docs\plans\MVP_BUILD_PLAN.md` (revision 3), all of it. It is the specification; this brief only scopes your part.
2. `docs\handoffs\2026-11-02_antigravity\01_ORCHESTRATION.md`.
3. The read-first list in section 2 of the plan.

## Rules that do not bend
Section 3 of the plan, every rule, with no exceptions. In particular: never open, list, search or print a SEALED or SPOILERS folder; no pushes; no network; stage by explicit path; no amend, rebase, reset --hard, clean or force; never delete outside plan rule 5.

## Decision rules (so you never need to ask)
- A step already done whose check still passes: log `ALREADY DONE <step>` and continue.
- Counts differ from Entry 024 but everything passes: record the new counts; it is not a failure.
- `docs\CODEBASE_STATE.md` was modified by someone else: append only, never rewrite.
- The repository root is `D:\Project Recess` rather than the project folder: work from the project folder, record the root in STATUS, and create worktrees at `D:\pmm-worktrees\b` and `D:\pmm-worktrees\c` (outside any working tree).
- A merge conflicts only in a log or STATUS file: keep both sides. A conflict in logic: STOP.
- Anything else not covered: the simpler option that keeps every gate green; log it.

## Ordered work
1. Pre-flight seal check: confirm, without opening anything, that no folder inside the project folder has SEALED or SPOILERS in its name. If one exists, STOP and report its path.
2. Phase A, steps A1 to A5 exactly as the plan says, including the documentation commit in A4 and the branches and worktrees in A5.
3. Create `docs\reports\2026-11-02_STATUS.md` and write `A DONE`, with each worktree's project folder.
4. Wait. When the Engine Wright's gate report exists and the Auditor's verdict for gate-B is `CLEAR`, merge `build/mvp-b` into `build/mvp`, run the readout and Desk tests on `build/mvp`, and write `B MERGED`.
5. Wait. When the Auditor's verdict for gate-C is `CLEAR`, merge `build/mvp-c` into `build/mvp`, run the readout, Desk tests, taste readout and kit tests, and write `C MERGED`.
6. Phase D, steps D2 to D5.

## Acceptance checks
- `gate-A` exists; `build/mvp`, `build/mvp-b` and `build/mvp-c` exist; both worktrees pass the readout.
- The backup bundle verifies, and its clone passes the Desk tests and the readout.
- After each merge, every readout passes on `build/mvp`.
- `git diff --name-only gate-A..build/mvp` lists only files allowed in phases B and C.
- No push was run, by you or any other agent (check every build log and the session's command history).

## Report format (Phase D, under 40 lines)
1. Counts: readout, unit tests, Desk tests, taste readout, kit tests (scripts and checks).
2. Gates: A, B, C, each PASS with its tag, and each Auditor verdict.
3. Decisions: one line each, from all three build logs.
4. OPEN risks carried forward (from C8, C10 and the Auditor).
5. The PowerShell commands to play CASE-FIX-03 in Firefox and to return to the default.
6. The Living Log entry draft, as text, not posted.
7. Last line: `VERDICT SAFE TO MERGE` or `VERDICT HOLD <single reason>`.

## Stop
Stop at any condition in plan section 5. At a stop: write the log line, write `STOP Warden <reason>` in STATUS, report, and wait. Never merge into `main` or `master`, and never push.
