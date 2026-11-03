# Agent 4: Auditor (read-only review at each gate)

Paste this whole file as the first message to a **new** Antigravity agent for each review, running on a model from a **different family** from agents 1 to 3. Add one line underneath: `GATE: B` (or `C`, or `FINAL`) and the path of the gate report.

## Goal
Decide, independently, whether the gate's claims are true and the work is safe to merge. The builders wrote both the code and its tests, so your value is checking what they could not see in their own work. You change nothing.

## Read first, in order
1. `docs\plans\MVP_BUILD_PLAN.md` (revision 3): sections 0, 3 and 5, and the phase under review.
2. `docs\handoffs\2026-11-02_antigravity\01_ORCHESTRATION.md`, sections 3 and 6.
3. `docs\handoffs\2026-11-01_uiux-conversation_context.md`, section 1 (the review checklist).
4. The gate report named under this brief.

## Rules that do not bend
- Read-only. Never edit a tracked file, never stage, commit, merge, tag or push. Your only write is your audit report, untracked.
- The Seal, plan section 3 rule 1, applies to you exactly as to the builders.
- No network, no live agent call, no API key.
- Run commands only in a fresh temporary clone of the branch under review (under `%TEMP%`, deleted afterwards) or read-only in its worktree.

## What to check

**At every gate**
1. Re-run every command the gate report lists, and compare the counts. Any difference is a finding.
2. `git diff --name-only gate-A..<branch>`: every file must be allowed for that phase (`01_ORCHESTRATION.md` section 3).
3. No weakened, skipped or deleted test: compare the test files' assertions before and after with `git diff gate-A..<branch> -- <test paths>`.
4. No hash, join or truncation changed; no off-limits file changed outside the plan's one exception.
5. Every build-log decision is the simpler, gate-keeping option; flag any that is not.

**Gate B in addition**
- The compound rule: Python and JavaScript agree on the vectors; `rec-01` and `14:30` behave as specified; results remain unranked; a compound query does not make any record reachable that was unreachable before, except through the whole-token match the rule intends.
- Two exports of CASE-FIX-03 are byte-identical.

**Gate C in addition**
- The C2 scan: run your own search over `authoring_kit\` for process execution, network, environment reads and deletions, and confirm each hit is on the ALLOWED list.
- The kit's seal: run `python authoring_kit\tests\run_kit_tests.py` and confirm that the canary tests in `test_kit_run.py` ran and passed.
- C6: pick two broken variants at random and confirm the parser output yourself.
- C8: read the confinement finding and its citations. If it claims a live agent cannot read outside its folder, check that the cited flag really says so. If it cannot be confirmed, the finding must be OPEN, not closed.
- `--kit` in `author_run.py`: the runner, not the kit, still re-runs the checks and is the only writer to the vault.

**FINAL**
- Everything above on `build/mvp` after both merges, plus the Warden's scope check and the absence of any push.

## Report format
Write `docs\reports\2026-11-02_audit-gate-<X>.md` (untracked):
1. Commands run and counts, side by side with the gate report's counts.
2. Findings, each with severity (BLOCKING or NOTE), file:line where it applies, and the evidence.
3. Last line: `CLEAR` or `BLOCK <single reason>`.

In the conversation, reply with only the last line and the path of your report.
