# Tests

Plain scripts; no test framework. Each prints `<name>: N of M checks passed` and exits 0 only when every check passes.

```powershell
python authoring_kit\tests\run_kit_tests.py
```

Expected output (the counts from the kit author's own run, in a Linux container with Python 3.13; not yet run on Windows):

```
PASS test_kitlib: 40 of 40 checks passed
PASS test_compat_check: 16 of 16 checks passed
PASS test_seed_sampler: 214 of 214 checks passed
PASS test_case_checks: 63 of 63 checks passed
PASS test_voice_lint: 50 of 50 checks passed
PASS test_repair_budget_taste: 37 of 37 checks passed
PASS test_brief_builder: 18 of 18 checks passed
PASS test_probe: 7 of 7 checks passed
PASS test_kit_run: 117 of 117 checks passed
PASS test_media: 83 of 83 checks passed
KIT TESTS 10 of 10 scripts passed
```

That is 700 checks in total (kit v4.2).

## Fixtures (all nonsense)

- `fixtures\engine_root\`: a fake engine with a case schema, skin schema and vocabulary (ESTABLISHES, CONTRADICTS, MASKS, REFRAMES and a defeat field, but none of the research's other relations, no aliases and no fragments), four rules, a contract, a readme, CASE-FIX-01, SKIN-FIX_A and a fake `check_case.py`. The fake fails FP-02 on the string `FORCE-FAIL-FP02`, DK-01 on an empty record title, and FP-03 on an observation of fewer than two words. FP-03 is the stand-in for a real rule that needs prose, so a placeholder skeleton trips it.
- `fixtures\fake_agent.py`: copies canned outputs for its unit (folders included, so S1's `bible_parts\`), records which secret-looking variables reached it, prints a canary on stdout and stderr, and simulates a usage-limit stop when a `_pause_<unit>` file is present. A `_raw_<unit>` folder is copied byte for byte (cut-off and byte-order-mark files), and a `_result_<unit>` file sets the result word it reports (`error_max_turns` exits 1; `denied` reports one permission denial).
- `fixtures\scenario.py`: builds a complete nonsense case for any seeds that passes every check. Prose carries `CANARY`; the sealed answer key carries `KEY_CANARY`.
- `fixtures\golden_mode_a.txt`: the exact screen output of a full Mode A run with seed 7, with the temporary stage root written as `<STAGE_ROOT>`. Rewrite it with `python test_kit_run.py --regold` only after a deliberate change.

## What each script proves

| Script | Proves |
|---|---|
| test_kitlib | The printer passes IDs, paths, trusted terms and numbers, and prints `WITHHELD` for anything else. Placeholder parsing, case rebuild, secret-variable stripping, and every message the code uses exists. |
| test_compat_check | Exact output on the fixture engine: 15 of 16 patterns available (3 NATIVE, 12 GENERIC), PAT-12 missing `accepted_fragment_orders`. A missing schema prints `COMPAT FAIL KT-CP-01` and exits 2; removing MASKS makes PAT-01 unavailable. |
| test_seed_sampler | Seed 7 gives PAT-05, MECH-09, RH-05, NP-3 and six named people. Over 200 seeds: distinct initials and sounds, no stock names, no unavailable pattern, one pattern (the MVP limit), valid critical strings. The ledger pushes recent seeds away, taste weights pull, and the ledger file holds no plain IDs or names. |
| test_case_checks | The scenario passes clean. Each bible and plan mutation fails exactly its intended check, including rule-passing name replacements (allowed), banned or colliding replacements (refused), declared tropes (exempt from the trope warning) and malformed trope declarations (refused), world documents without a purpose (KT-PL-18), depiction placeholders kept out of the case, voice samples, the flavor cap, the document count and the tier count. |
| test_voice_lint | Every clean fill passes; all eight voice exemplars pass their own profile's rules; each prose check fires on its trigger and stays quiet on near-misses. |
| test_repair_budget_taste | Engine output parsing (IDs and paths only, tolerated rules, crashes), the repair decision table, turn and cost caps, answer validation and taste updates. |
| test_brief_builder | Template filling, a missing token raises, every token in every prompt is supplied, check lists are stage-specific. |
| test_probe | The probe finds FP-03 as the only placeholder-caused rule, separates a fixture's own failures from placeholder effects, and prints IDs only. |
| test_kit_run | The golden Mode A transcript. Stage folders: outside the workspace, closed after acceptance, only the current unit on disk, the stage root removed at finish, a stage root inside the workspace refused. Canaries never on screen, in logs, in the ledger or in the project tree; the answer key never in S3 or S4 briefs; S3 briefs carry the neighbour index without facts. The media manifest is written, player-safe and consistent with the case text, and the S3 brief lists the printed values. Mode B flow, repair, abort on repeat, abort at the cap, budget stop, pause and resume, tolerance (FP-03 fails S2 without it), engine-rule repair, gate failure re-opening a closed unit, drift abort, setup errors, the review, the blind audit (pass, bad citations, giveaway options, same family refused, the shortcut probe never seeing records) and the estimate. |
| test_media | The registry is deterministic and seed-dependent; report numbers rise with filing date; badge numbers follow hiring order and expiry follows issue; newspaper issue numbers and weekdays are calculated; frames rise per camera; imprints and light follow the camera, climate and month. Wear never takes an artifact below the legibility floor. Each bad media declaration fails its own check (KT-MD-01 to 09), anomalies must be real and fact-bearing, missing or invented values and wrong weekdays are caught, the manifest holds no facts, roles, tiers or anomaly flags, and plates carry the same likeness for the same person. |

## The first real run, replayed (test_kit_run sections 15 and 16)

The 2026-11-02 run failed with `KT-BI-01 FAIL $`: S1 timed out with no file, and the repair wrote a bible that stopped mid-object at line 261. These sections replay it with nonsense: a facts part cut off after a comma, the agent reporting `error_max_turns`, and a one-part repair that passes. They check that the broken file is named with its line (never a bare `$`), that the result word and run time print while the planted text does not, that the other parts are already in place for the repair, that a bible repair gets 8 turns, and that the agent log keeps only numbers and one word. They also cover a missing part (KT-IO-01), a field set in two parts (KT-IO-03), a byte-order mark (accepted), a missing field (`$.cover`), an invented field (withheld from the screen), the single `bible.json` fallback, a timeout (cost reported as unknown) and a permission denial (counted, never shown).
| test_resume | Kit v4.2: S2 runs as S2A (plan) and S2B (engine files) with inputs inline and minified; every output is saved to `checkpoints/attempts/` before it is checked; an interrupted unit with saved work is checked, never re-run; resume after an abort or a budget stop keeps accepted units, resets repair rounds and starts a new budget pass; a run from before the split resumes at S2A; cleanup removes only old marked stage roots, unopened; preflight prints IDs and verdicts only. |
