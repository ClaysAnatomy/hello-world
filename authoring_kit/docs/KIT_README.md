# Authoring kit

A quality layer for sealed case authoring in Project Mystery Machine. It prepares each stage's inputs and brief, an agent writes, and the kit validates. It writes no story itself. It only adds files under `authoring_kit\`.

Start with `CRAFT_GUIDE.md` for the why. This file covers the how.

## Requirements

- Python 3.11 or later (tested here on 3.13), standard library plus `jsonschema`.
- The engine folder as described in `kit_config.json` (paths are relative to the project root).

```powershell
python -m pip install jsonschema
```

## Before the first run

```powershell
python authoring_kit\python\compat_check.py --root .
```

This prints `COMPAT PAT-nn AVAILABLE` or `UNAVAILABLE missing <engine term>` for all 16 aha patterns, then counts. It decides which patterns can be chosen. If an engine term has a different name from the one guessed in `data\capability_map.json`, edit that file, not the code.

## A run

The workspace is the sealed case folder: for this project, `<vault_dir>\<case_id>`. The kit never knows or prints a vault path.

```powershell
python authoring_kit\python\kit_run.py init --ws <case folder> --root . --brief <author brief file>
```

Mode A (headless; an agent command is set in `data\kit_config.json`):

```powershell
python authoring_kit\python\kit_run.py next --ws <case folder> --all
python authoring_kit\python\kit_run.py finish --ws <case folder>
```

Mode B (interactive; any agent follows `AGENT_PLAYBOOK.md`):

```powershell
python authoring_kit\python\kit_run.py next   --ws <case folder>
python authoring_kit\python\kit_run.py check  --ws <case folder>
python authoring_kit\python\kit_run.py repair --ws <case folder>
python authoring_kit\python\kit_run.py status --ws <case folder>
```

`--brief` is optional and can be one word or many pages. `--seed N` makes the seeds reproducible. `--review` adds the optional S6 craft review.

## Stages

| Stage | Writes | Sees | Checked by |
|---|---|---|---|
| S1 story and truth bible | `bible.json` | brief, seeds, pattern briefs, authoring contract | KT-BI-01..14, VL-02 |
| S2 document cut | `case.json`, `skin.json`, `clue_plan.json` with placeholders in every prose field | bible, forms, voices, contract, fixtures, engine schemas | KT-PL-01..15, engine checks |
| S3 one document at a time | `fill.json` | only that document's facts, author, reader, voice and world texture | KT-FL-01, VL-01..16 |
| S3 gate | nothing | all documents | VL-09 overlap, engine checks |
| S4 desk fields | `fill.json` | option gists without correctness, entities, desk facts | KT-FL-01, VL-04, VL-05 and the rest, engine checks |
| S5 repair | the target's outputs | failing IDs, paths and requirements only | the target's checks |
| S6 craft review (optional) | `review.json` | everything | KT-RV-01; prints scores |

`finish` rebuilds the case from the skeleton and the fills, confirms no placeholder remains, runs the engine checks again, writes `claims.json` (JSON path, owner and fact IDs for every text, for the later semantic audit), and appends salted seed hashes to the ledger.

## What it prints

Only fixed sentences from `data\messages.json`, with arguments that are IDs, JSON paths, trusted engine terms or numbers. Anything else prints as `WITHHELD`. Agent output is never written anywhere. Engine output is parsed in memory for rule IDs and paths, then dropped.

## Exit codes

0 pass, 1 a check failed (repair is possible), 2 setup error, 3 action needed (Mode B), 4 stopped (abort or budget).

## Economy

Each stage has a turn cap and the run has 80 (`limits.json`, inside the project's 80 turns and $6.00). When the agent reports no usage, each call is charged its full cap. Repairs see only IDs and paths, are capped at 2 rounds, and stop the run if the same check fails in consecutive rounds. Dollar caps are UNVERIFIED planning figures and apply only when the agent reports cost. The guard prints turn counts only.

## Files

- `data\`: every rule, list, limit, prompt token source and message. Edit freely.
- `prompts\`: the stage templates. `{{TOKENS}}` are filled from data. Replace the wording freely; keep the tokens.
- `python\`: `kitlib`, `compat_check`, `seed_sampler`, `ledger`, `brief_builder`, `case_checks`, `voice_lint`, `repair_builder`, `budget_guard`, `runners`, `kit_run`, `taste_bridge`.
- `tests\`: `python authoring_kit\tests\run_kit_tests.py`.
