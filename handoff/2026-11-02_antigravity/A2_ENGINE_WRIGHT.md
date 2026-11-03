# Agent 2: Engine Wright (Phase B)

Paste this whole file as the first message to a new Antigravity agent whose workspace is `D:\pmm-worktrees\b`. Start only after STATUS says `A DONE`.

## Goal
Finish bridge round two on branch `build/mvp-b`: confirm CASE-FIX-03 end to end, and add the compound-query rule (a compound term such as `rec-07` or `14:30` matches its whole indexed token, with the pieces as fallback), Python first, then the Desk. The Python is the specification.

## Read first, in order
1. `docs\plans\MVP_BUILD_PLAN.md` (revision 3): sections 0 to 3, Phase B, and section 5.
2. `docs\handoffs\2026-11-02_antigravity\01_ORCHESTRATION.md`, especially section 3 (what you may edit).
3. `docs\handoffs\2026-11-01_uiux-conversation_context.md`, section 1 (your review checklist) and section 5 (the detailed brief for this phase).
4. The engine's tokenizer, search and lint modules, the search tests, the Desk's `client\js\search.js` and `client\js\tokenizer.js`, and how the vectors in `client\tests\vectors\` are generated from Python.

## Rules that do not bend
Section 3 of the plan. In particular: never change any hash, join or truncation; edit `tokenizer.js`, `search.js` and the vectors only for the compound rule; regenerate vectors from Python, never by hand; never weaken or delete a test.

## Decision rules (so you never need to ask)
- B1, B3 or B6 already done and passing: log `ALREADY DONE`, keep the check in your gate report, build nothing.
- B4 needs more than about 40 changed lines: skip it and log the decision.
- The compound rule needs a change to an off-limits file other than `tokenizer.js`, `search.js` or the vectors: STOP and report file and line numbers.
- Python and JavaScript disagree on any vector: the Python is right; fix the JavaScript.
- Anything else: the simpler option that keeps every gate green; log it.

## Ordered work
1. Confirm your worktree's project folder (from STATUS) and run the readout and Desk tests once, recording the counts.
2. B1, B2, B3.
3. B5, in this order: Python tokenizer and search, the reachability computation in `lint.py`, tests for `rec-01` and `14:30` (whole-token match first, pieces as fallback, results unranked as before), regenerate the vectors, port to `search.js` and `tokenizer.js`, Desk tests.
4. B6, then B4.
5. GATE B exactly as the plan states. Write `docs\reports\2026-11-02_gate-B.md` (commands, exact counts, `git diff --name-only gate-A..HEAD`, ALREADY DONE items). Commit by explicit path. Tag `gate-B`.

## Acceptance checks
- Readout passes with the new counts; Desk tests pass.
- Two exports of CASE-FIX-03 are byte-identical.
- Contract freshness passes; the forbidden-pattern scan on `client\` is 0.
- The diff touches only files listed for you in `01_ORCHESTRATION.md` section 3.

## Report format (under 25 lines)
Counts before and after; each step as PASS, ALREADY DONE or SKIPPED with a one-line reason; files changed; decisions; anything OPEN. Last line: `GATE B READY` or `GATE B BLOCKED <reason>`.

## Stop
Stop at any condition in plan section 5. Never merge your branch yourself, never push, and never touch the Kit Integrator's files.
