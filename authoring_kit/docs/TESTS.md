# Tests

Plain scripts; no test framework. Each prints `<name>: N of M checks passed` and exits 0 only when every check passes.

```powershell
python authoring_kit\tests\run_kit_tests.py
```

Expected output (the counts as written by the kit author's own run, in a Linux container with Python 3.13; not yet run on Windows):

```
PASS test_kitlib: 30 of 30 checks passed
PASS test_compat_check: 13 of 13 checks passed
PASS test_seed_sampler: 212 of 212 checks passed
PASS test_case_checks: 42 of 42 checks passed
PASS test_voice_lint: 47 of 47 checks passed
PASS test_repair_budget_taste: 27 of 27 checks passed
PASS test_brief_builder: 16 of 16 checks passed
PASS test_kit_run: 53 of 53 checks passed
KIT TESTS 8 of 8 scripts passed
```

## Fixtures (all nonsense)

- `fixtures\engine_root\`: a fake engine with a case schema, skin schema, vocabulary (with ESTABLISHES, CONTRADICTS, MASKS, REFRAMES and no aliases or fragments), three rules (FP-01, FP-02, DK-01), a contract, a readme, CASE-FIX-01, SKIN-FIX_A, and a fake `check_case.py`. The fake prints `FP-02 FAIL <path>` when any string contains `FORCE-FAIL-FP02`, and `DK-01 FAIL` when a record title is empty.
- `fixtures\fake_agent.py`: copies canned outputs for its unit, records which secret-looking variables reached it, and prints a canary on stdout and stderr.
- `fixtures\scenario.py`: builds a complete nonsense case for any seeds that passes every check. Prose carries `CANARY`; the sealed answer key carries `KEY_CANARY`.
- `fixtures\golden_mode_a.txt`: the exact screen output of a full Mode A run with seed 7 (108 lines). Rewrite it with `python test_kit_run.py --regold` only after a deliberate change.

## What each script proves

| Script | Proves |
|---|---|
| test_kitlib | The printer passes IDs, paths, trusted terms and numbers, and prints `WITHHELD` for anything else (story text, word-shaped IDs, unknown path keys). Placeholder parsing, case rebuild with paths, secret variable stripping, and every message the code uses exists. |
| test_compat_check | Exact output on the fixture engine (13 of 16 available; PAT-06 and PAT-07 missing `aliases`, PAT-12 missing `accepted_fragment_orders`), a missing schema prints `COMPAT FAIL KT-CP-01` and exits 2, and removing MASKS makes PAT-02 unavailable. |
| test_seed_sampler | Seed 7 gives exactly PAT-05 and PAT-11, MECH-06, RH-03, NP-2 and the names Ivo Fiala, Miroslav Dvorak, Teodora Adamczyk, Kazimierz Lisowski and Franziska Vrba. Over 200 seeds: distinct initials and sounds, no stock names, no unavailable pattern, limits respected, valid critical strings. The ledger pushes recent seeds away, taste weights pull, and the ledger file holds no plain IDs or names. |
| test_case_checks | The scenario passes clean; each of 15 bible and 23 plan mutations fails exactly its intended check IDs; warnings never fail. |
| test_voice_lint | Every clean fill passes, every voice exemplar passes its own voice rules, and each prose check fires on its trigger and stays quiet on near-misses ("no clue to the fault" is allowed). |
| test_repair_budget_taste | Engine output parsing (IDs and paths only, tolerated rules, crashes), the repair decision table, the failures table, turn and cost caps, budget printing, answer validation (text refused) and taste updates. |
| test_brief_builder | Template filling, a missing token raises, every token in every prompt is supplied, and check lists are stage-specific. |
| test_kit_run | The golden Mode A transcript; canaries never on screen, in logs, in the ledger or in the project tree; the answer key never in S3 or S4 folders; S3 folders hold only the fill schema; no secret variable reaches the agent; Mode B flow; repair success; abort on repeat; abort at the cap; budget stop leaves the run resumable; engine rule failure and repair; engine drift abort; setup errors; the optional review accepts scores and refuses text. |

## Key exact lines

- Repair: `CHECK VL-01 FAIL PP-CLUE-04-2`, `CHECK S3-CLUE-04 FAIL`, `REPAIR S3-CLUE-04 round 1 READY`.
- Abort on repeat: `ABORT S3-CLUE-04 same check failed in consecutive rounds`, then `ABORT check VL-01`.
- Abort at cap: `ABORT S3-CLUE-04 repair rounds exhausted`, then `ABORT check VL-12`.
- Budget: `BUDGET STOP S3 stage turn cap reached`, `BUDGET S3 turns 3 of 3`, `BUDGET run turns 25 of 80`.
- Drift: `ABORT engine files changed since init`, `ABORT check KT-RN-02`.
- Mode B: `NEXT S1 READY`, `PROMPT stages/S1/prompt.md`.
