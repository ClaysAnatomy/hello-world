# Agent 3: Kit Integrator (Phase C)

Paste this whole file as the first message to a new Antigravity agent whose workspace is `D:\pmm-worktrees\c`. Start only after STATUS says `A DONE`.

## Goal
Bring the authoring kit into the project on branch `build/mvp-c`, prove on Windows and against the real engine that it does what it claims, wire it into the sealed runner behind `--kit`, and prove the whole chain with the fake agent. The kit is the quality layer that will make the first real case good. Your job is to make it trustworthy, not to extend it.

## Read first, in order
1. `docs\plans\MVP_BUILD_PLAN.md` (revision 3): sections 0 to 3, Phase C, and section 5.
2. `docs\handoffs\2026-11-02_antigravity\01_ORCHESTRATION.md`, especially sections 2 and 3.
3. After C1: the kit's `docs\KIT_README.md`, `docs\INTEGRATION.md`, `docs\TESTS.md`, `docs\AGENT_PLAYBOOK.md` and `docs\CRAFT_GUIDE.md`.
4. `taste\tools\author_run.py`, `taste\rules\authoring.json`, `engine\tools\check_case.py`, `engine\README_AUTHORING_FOR_OPUS.md`, `engine\contract\bundle_contract.json`.

## Rules that do not bend
Section 3 of the plan. In particular: the security scan (C2) comes before any copy; no live agent call of any kind (the fake agent only); no API key; stage by explicit path; never weaken a kit test or an engine test.

## Decision rules (so you never need to ask)
- A scan hit that is not on the C2 ALLOWED list: STOP. Do not judge it harmless yourself.
- A kit test fails on Windows only: fix the kit if the fix is small and local (paths, line endings, encoding), log it with file:line, and rerun the whole suite. Otherwise STOP.
- `compat_check` finds a native relation missing: record it as a PROPOSED ADDITION; do not change the engine schema.
- The parser test (C6) fails for one variant: fix `engine_output` settings or the parser if the fix is under about 20 lines; otherwise STOP.
- A Claude Code flag or usage-limit signal you cannot confirm from its documentation or `--help`: write it as UNVERIFIED and do not rely on it.
- C12 needs the compound-query rule: do C1 to C11, then wait for STATUS `B MERGED`, then `git merge build/mvp` into your branch (merge commit), rerun the kit tests, and continue.
- Anything else: the simpler option that keeps every gate green; log it.

## Ordered work
1. Confirm your worktree's project folder (from STATUS); run the readout once and record the counts.
2. C1 to C11 exactly as the plan states. For C8, C9 and C10, the kit already has the behaviour: your job is to prove it on Windows, configure it from the real documentation, and record what you read.
3. Wait for `B MERGED`. Merge `build/mvp` into `build/mvp-c`.
4. C12 and C13.
5. GATE C exactly as the plan states. Write `docs\reports\2026-11-02_gate-C.md` (commands, exact counts, C2 scan table, C5 availability table, C6 parser table, C8 confinement finding with citations, C9 estimates, C10 signals, files changed). Commit by explicit path. Tag `gate-C`.

## Acceptance checks
- C2: every scan hit is ALLOWED.
- C4: 9 of 9 kit scripts pass on Windows (496 checks), or every difference is explained and fixed.
- C6: every broken variant yields its own rule ID and path; clean fixtures yield nothing.
- C7: S4 and finish run the full check; tolerance applies only at S2 and the S3 gate.
- C8: no stage folder under any workspace; at most one unit folder under the stage root at a time.
- C12: the full fake chain exports a case that round-trips with 0 missing fields.
- C13: the audit dry run prints only verdicts, numbers and IDs, and the shortcut stage folder holds no records.

## Report format (under 30 lines)
Counts; each step as PASS, ALREADY DONE, OPEN or SKIPPED with a one-line reason; the pattern availability summary (`n of 16`, NATIVE and GENERIC counts); OPEN risks; files changed; decisions. Last line: `GATE C READY` or `GATE C BLOCKED <reason>`.

## Stop
Stop at any condition in plan section 5. Never merge your branch into `build/mvp` yourself, never push, and never touch the Engine Wright's files.
