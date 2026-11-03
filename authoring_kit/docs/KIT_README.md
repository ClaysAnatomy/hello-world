# Authoring kit

A quality layer for sealed case authoring in Project Mystery Machine. It prepares each stage's inputs and brief, an agent writes, and the kit validates. It writes no story itself. It only adds files under `authoring_kit\`.

Start with `CRAFT_GUIDE.md` for the why. This file covers the how. The kit follows *Mystery Engine Design Research* (Tracks 3, 5 and 6) for its aha patterns, voice and bias matrix, failure modes and blind audit.

## Requirements

- Python 3.11 or later (tested on 3.13), standard library plus `jsonschema`.
- The engine folder as described in `data\kit_config.json` (paths are relative to the project root).

```powershell
python -m pip install jsonschema
```

## Before the first run

```powershell
python authoring_kit\python\compat_check.py --root .
python authoring_kit\python\placeholder_probe.py --root . --case engine\fixtures\CASE-FIX-03\case.json --skin engine\fixtures\skins\SKIN-FIX_A.json
python authoring_kit\python\kit_run.py estimate --documents 10
```

- `compat_check` prints each of the 16 patterns as `AVAILABLE NATIVE` (the engine has the research's own relation), `AVAILABLE GENERIC` (expressible through a general relation such as REFRAMES) or `UNAVAILABLE missing <term>`. If an engine term has a different name, edit `data\capability_map.json`, not the code.
- `placeholder_probe` lists the engine rules that fail only because S2 writes placeholders instead of prose. Add `--write` to put them in `limits.json` → `tolerated_engine_rules`. Tolerance applies at S2 and the S3 gate only; S4 and finish always run the full check.
- `estimate` prints agent invocations and turns at cap for a case of that size, against the caps.

## A run

The workspace is the sealed case folder: for this project, `<vault_dir>\<case_id>`. The kit never knows or prints a vault path. Stage folders, where agents work, are created **outside** the workspace (a new folder under the system temp directory unless `--stage-root` says otherwise). Each one is deleted as soon as its unit is accepted, after a copy is archived in the workspace under `checkpoints\units\`. At any moment the only stage folder on disk is the unit being worked on.

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

Blind audit, after `finish` and after the engine has packed the player bundle:

```powershell
python authoring_kit\python\kit_run.py audit --ws <case folder> --bundle <player bundle json>
python authoring_kit\python\kit_run.py audit-score --ws <case folder>
```

`--brief` is optional and can be one word or many pages. `--seed N` makes the seeds reproducible. `--review` adds the optional S6 craft review.

## Stages

| Stage | Writes | Sees | Checked by |
|---|---|---|---|
| S1 story and truth bible | five parts in `bible_parts\`, joined by the kit into `checkpoints\bible.json` | brief, seeds, pattern brief, authoring contract | KT-IO-01..03, KT-BI-01..15, VL-02 |
| S2 document cut | `case.json`, `skin.json`, `clue_plan.json` with a placeholder in every prose field | bible, forms, voices, contract, fixtures, engine schemas | KT-PL-01..17, engine checks (with tolerated rules) |
| S3 one document at a time | `fill.json` | that document's facts, author sheet and voice sample, reader, voice profile, world texture, a facts-free index of the other papers | KT-FL-01, VL-01..17 |
| S3 gate | nothing | all documents | VL-09 overlap, engine checks (with tolerated rules) |
| S4 desk fields | `fill.json` | option gists without correctness, entities, desk facts | KT-FL-01, VL checks, full engine checks |
| S5 repair | the target's outputs, starting from the previous ones already in place | failing IDs, files, lines, paths and requirements only | the target's checks; turns capped by the target stage (`limits.json` → `turns.repair_unit_caps`) |
| S6 craft review (optional) | `review.json` | everything | KT-RV-01; prints scores |
| S7 blind audit (after finish) | `answers.json`, twice | SHORTCUT: questions and options only. SOLVE: the player bundle only | AU-01 solve, AU-02 citations, AU-03 shortcut |

`finish` rebuilds the case from the skeleton and the fills, confirms no placeholder remains, runs the engine checks again, writes `claims.json` (JSON path, owner and fact IDs for every text, for the later semantic audit), appends salted seed hashes to the ledger, and removes the stage root.

## The blind audit

S7 follows the research's Gates 3 and 4: an agent of a **different model family** from the author (`agent.family` and `audit_agent.family` in `kit_config.json` must both be set and differ) first tries to guess the answers from the options alone, then solves the case cold from the player bundle with the Four-Stage Detective Protocol. The kit scores both against the sealed key and prints only verdicts, numbers and IDs. Citations pass when every cited record is valid for the answer and together they cover every supporting fact; the research's Jaccard figure is reported too. Leave-one-out ablation and order-shuffle runs (Gates 5 and 6) are not built yet.

## What it prints

Only fixed sentences from `data\messages.json`, with arguments that are IDs, JSON paths, trusted engine terms, paths the kit created, or numbers. Anything else prints as `WITHHELD`. Agent output is never written anywhere; it is held in memory only to read numeric usage fields and to recognise a usage-limit stop. Engine output is parsed in memory for rule IDs and paths, then dropped.

## Exit codes

0 pass, 1 a check failed (repair is possible), 2 setup error, 3 action needed (Mode B), 4 stopped (abort or budget), 5 paused (a usage limit was reached; run `next` again later and the same unit restarts, with no repair round used).

## Economy

Each stage has a turn cap and the run has 80 (`limits.json`, inside the project's 80 turns and $6.00). When the agent reports no usage, each call is charged its full cap. Repairs see only IDs and paths, are capped at 2 rounds, and stop the run if the same check fails in consecutive rounds. The MVP settings are one aha pattern and 6 to 12 documents. Dollar caps are UNVERIFIED planning figures and apply only when the agent reports cost. The guard prints turn counts only.

## Files

- `data\`: every rule, list, limit, prompt token source and message. Edit freely.
- `prompts\`: the stage templates. `{{TOKENS}}` are filled from data. Replace the wording freely; keep the tokens.
- `python\`: `kitlib`, `compat_check`, `placeholder_probe`, `seed_sampler`, `ledger`, `brief_builder`, `case_checks`, `voice_lint`, `repair_builder`, `budget_guard`, `runners`, `kit_run`, `taste_bridge`.
- `tests\`: `python authoring_kit\tests\run_kit_tests.py`.
