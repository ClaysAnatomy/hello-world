# MVP BUILD PLAN: Project Mystery Machine (revision 3, 2026-11-02)

Save as `D:\Project Recess\Project Mystery Machine\docs\plans\MVP_BUILD_PLAN.md`. Story-free. Written for models with local file and terminal access (the executors). It is split across four agents; `01_ORCHESTRATION.md` says which agent runs which phase. Aetherius reads one summary at the end.

Revision 3 changes from revision 2 are marked **[R3]**. In short: the authoring kit already implements the stage-folder isolation, per-stage model and effort, usage-limit pause, placeholder probe and blind audit that revision 2 asked the builder to write, so Phase C now **verifies and wires** those pieces instead of building them.

## 0. Settings Aetherius fills in before handing this over

```
BACKUP_PATH      = <a folder on a physical drive that is neither D: nor H:, e.g. E:\Backups\MysteryMachine>   (blank = STOP at A3)
REPO_URL         = https://github.com/ClaysAnatomy/hello-world.git
KIT_BRANCH       = claude/eager-davinci-qgiihc
KIT_COMMIT       = 1322aa699ce8edc7a82fdf1bf6189adaa5746476
COMPOUND_QUERY   = YES        (LOCKED, Entry 024: a compound term such as rec-07 matches its whole indexed token, pieces as fallback)
```

**[R3]** KIT_COMMIT is the reviewed kit commit. The branch may carry later commits (this handoff pack, for example); C1 checks out exactly KIT_COMMIT.

The GitHub repository is public. Nothing in it is story or secret; Aetherius decides whether to make it private. The plan does not depend on that choice.

Handing over this plan authorizes: commits on the work branches named in `01_ORCHESTRATION.md` at green gates, merges between those branches, and git worktrees under `D:\pmm-worktrees\`. It does not authorize: pushes, amending, rebasing, deleting anything outside the paths in rule 5, any live authoring run, any live agent call, any image run, or applying the look.

## 1. Who you are and how you work

You are a builder on a small team. Everything you need is in this repo and in the files listed in section 2. Do not ask Aetherius questions. Where a decision is not covered, take the simpler option that keeps every gate green, record it in your build log, and go on. Stop only at the STOP conditions in section 5. Keep your own build log at `docs\reports\2026-11-02_build-log_<agent>.md`: one line per decision, per gate and per stop. Only agent 1 writes `docs\reports\2026-11-02_STATUS.md`.

Several steps may already be done: Entry 024 reports commits ec09a42, 1e6597e, 485ec61, da6ab51 and 24474c4, a backup to H:, and CASE-FIX-03 built. Before each step, check `git log`, `git status` and the files. If a step is already done and its check still passes, log `ALREADY DONE <step>` and move on. "Already done" never skips the check itself.

## 2. Read first (in this order, before any change)

1. `README.md` and `docs\CODEBASE_STATE.md` (check its modified time; it may hold another session's uncommitted edits; append only, never overwrite).
2. `docs\handoffs\2026-11-01_uiux-conversation_context.md`. Its section 1 is the review checklist you apply to your own results; its section 5 is the detailed brief for Phase B. Where it says "ask" or "wait for Aetherius", this plan's STOP list governs.
3. `docs\handoffs\2026-11-01_cowork_project-handoff.md`.
4. `engine\docs\BUNDLE_CONTRACT.md` and `engine\contract\bundle_contract.json`.
5. `engine\README_AUTHORING_FOR_OPUS.md`, `taste\tools\author_run.py`, `engine\tools\check_case.py`.
6. `docs\handoffs\2026-11-02_antigravity\01_ORCHESTRATION.md` and your own agent brief.
7. Living Log: only if it is already readable through a connected tool with no new sign-in. Otherwise skip it and log `LOG NOT READ`. Do not open a browser or network connection for it (rule 4).

## 3. Rules that do not bend

1. **The Seal.** Never open, list, search or print anything under `D:\_SEALED_DO_NOT_OPEN\` or any folder whose name contains SEALED or SPOILERS. Exception: kit files whose name contains `header_sealed` (a prompt template). Never write story. Every fixture is nonsense. Print only names, IDs, counts, pass/fail and command output. **[R3]** If you find a SEALED or SPOILERS folder inside the project folder or a worktree, do not open it: STOP and report its path (section 5, item 9).
2. **The Python is the specification.** Never change any hash, join or truncation. Off limits unless a phase says otherwise: `client\js\hash.js`, `tokenizer.js`, `search.js`, `verifier.js`, `scheduler.js`, `saves.js`, `state.js`, `correspondent.js`, `client\tests\vectors\`.
3. **Fair play.** Delay is pacing, never a gate. A slip never reveals whether it matched. No sealed content in any Desk file. No fact lives only in pixels or audio. All wording comes from data. Rules, prompts and vocabulary are data files.
4. **No network** except the single `git clone` in C1. No API keys: never read, enter or store one. No pushes. No browser.
5. **Deletion** is allowed only for: temp folders this plan creates under `%TEMP%`; anything under `incoming\`; `client\data\current.case.js` (gitignored; created and removed by this plan); the kit's own stage folders (it deletes them itself, fenced by the `.mm_kit_stage_root` marker); and worktrees under `D:\pmm-worktrees\` removed with `git worktree remove` at the end. Archive, never delete, anything else. No `git add .`: stage by explicit path. No amend, rebase, reset --hard, clean or force. After A5, never commit to the branch that was current before A5.
6. **No live runs.** Never run a real authoring run, an image run or a live agent probe. The fake agent only.
7. **Green stays green.** Existing gates stay green at every step. Do not weaken or delete a test to make it pass.
8. **[R3] Stay in your lane.** Edit only the files your phase allows (`01_ORCHESTRATION.md` section 3). Another agent's files are read-only to you.

## 4. The phases

### Phase A: verify and secure (agent 1)

* A1. Run `python engine\tests\run_dod_checks.py`. Pass means every check passes, whatever the count; Entry 024 reports 10/10 with 153 unit tests. Record the actual counts. Any failure: STOP. **[R3]** Also run `node client\tests\run_tests.js` and the taste readout, and record those counts.
* A2. If the three groups (a: schema fields, DK-01..05, desk defaults, fixtures and broken variants; b: exporter, round trip, contract bridge; c: authoring README and `--export-desk`) are already committed (Entry 024: ec09a42, 1e6597e, 485ec61), log ALREADY DONE. Otherwise map them by explicit path; expected counts 35, 12, 3.
* A3. Backup. Confirm the destination drive letter is neither D: nor H: and report it. Run `git bundle create "%BACKUP_PATH%\mysterymachine-<date>.bundle" --all`, then `git bundle verify`, then clone the bundle to a temp folder under `%TEMP%`, run `node client\tests\run_tests.js` and `python engine\tests\run_dod_checks.py` there, report both pass counts, and delete the temp folder. If BACKUP_PATH is blank, D: or H:, STOP. Do not push anywhere.
* A4. Commit anything from A2 that is still uncommitted, one commit per group, by explicit path, with messages that describe only what was checked. **[R3]** Then commit `docs\plans\MVP_BUILD_PLAN.md` and `docs\handoffs\2026-11-02_antigravity\` as one documentation commit.
* A5. Tag `gate-A`. Create `build/mvp` from here. **[R3]** Create `build/mvp-b` and `build/mvp-c` from `gate-A`, and add the worktrees `D:\pmm-worktrees\b` (on `build/mvp-b`) and `D:\pmm-worktrees\c` (on `build/mvp-c`). The repository may be rooted at `D:\Project Recess` (Entry 004), in which case the project sits at `<worktree>\Project Mystery Machine\`; use `git rev-parse --show-toplevel` and record the project folder for each worktree in STATUS. Run the readout once in each worktree's project folder to prove it is complete. Write the first STATUS entry.

### Phase B: bridge round two (agent 2, in worktree b, on `build/mvp-b`)

Entry 024 reports CASE-FIX-03 built (17/17 rules, 3-of-3 round trip, byte-identical exports, no hard-coded "three" in the Desk JS) and DK-01 already treating `after_clue_id` as a dependency. For each, run its check and log ALREADY DONE if it passes; build only what is missing.

* B1. CASE-FIX-03: three questions; passes all 17 rules; exports and round-trips with 3 entries verified; included in the readout.
* B2. Print the exact PowerShell commands to export it to `client\data\current.case.js` and to delete that file again.
* B3. Confirm the Desk takes its entry count and wording from the case. If a logic change is needed in an off-limits file, STOP and report line numbers.
* B4. Optional `clue_id` on image briefs (skip if it needs more than about 40 changed lines; log the decision).
* B5. Compound query rule: Python first (tokenizer, search, the reachability computation in `lint.py`), regenerate the vectors, then port to `client\js\search.js`, with tests for `rec-01` and `14:30`. This is the only step allowed to edit `tokenizer.js`, `search.js` and their vectors, and only for this rule.
* B6. Confirm a mail delivered after a clue is opened counts as a reachability dependency in DK-01, with a broken variant.
* GATE B: readout passes with the new counts; Desk tests pass; two exports of CASE-FIX-03 are byte-identical; contract freshness passes; the forbidden-pattern scan on `client\` is 0. Commit by explicit path and tag `gate-B`. Then the Auditor reviews (section 6 of `01_ORCHESTRATION.md`) before agent 1 merges.

### Phase C: import and wire the authoring kit (agent 3, in worktree c, on `build/mvp-c`)

* C1. `mkdir incoming`, then `git clone --branch %KIT_BRANCH% %REPO_URL% incoming\authoring_kit_from_github`, then `git -C incoming\authoring_kit_from_github checkout --detach %KIT_COMMIT%` and confirm `git -C incoming\authoring_kit_from_github rev-parse HEAD` equals KIT_COMMIT. If not, STOP. Add `incoming/` to the project `.gitignore`. Report the repository as public unless the clone required sign-in.
* C2. **[R3]** Security scan of `incoming\authoring_kit_from_github\authoring_kit` before copying anything. Search for network use, process execution (`subprocess`, `os.system`, `eval`, `exec`, `__import__`), environment reads, deletions (`rmtree`, `unlink`, `remove`), absolute paths, drive letters, `..`, profile paths and vault-like names. List every hit as file:line and classify each as ALLOWED or UNEXPECTED. ALLOWED, and only these:
  - `python\runners.py`: `subprocess.run` for the agent command template (`agent` or `audit_agent` in `kit_config.json`) and for the engine check commands (`engine_checks`).
  - `python\kitlib.py`: `child_env()` copies the environment only to remove names ending in a listed suffix before a child process starts.
  - `python\kit_run.py`: `tempfile.mkdtemp` for the stage root; `shutil.rmtree` only on folders inside a stage root that carries `.mm_kit_stage_root`, on the stage root itself at finish (same marker check), and on `checkpoints\units\<unit>` inside the workspace before re-archiving; `unlink` of a stale fill under the workspace's `checkpoints\fills\`.
  - `python\brief_builder.py`: `shutil.rmtree` of a stage folder only when its parent carries the marker.
  - `python\placeholder_probe.py`: `tempfile.mkdtemp` and `shutil.rmtree` of its own temporary folder.
  - `tests\`: `subprocess` in `run_kit_tests.py`, `kit_test_util.py` and through the kit; `tempfile` folders; the fake agent; test-only fake variables named `KITTEST_API_KEY`, `KITTEST_AUTH_TOKEN`, `X_API_KEY`, `Y_AUTH_TOKEN` with fake values.
  - Writes: the workspace passed with `--ws`, the stage root, `authoring_kit\state\` under `--root`, and `authoring_kit\data\limits.json` only through `placeholder_probe.py --write`.
  - Words: "vault", "sealed", "SEALED" and "spoiler" where they describe the seal in documentation, docstrings, prompt text, messages and the file name `header_sealed.md`. They are references, never paths, and the kit contains no drive letter.

  Network calls, `eval`, `exec`, `os.system`, `__import__`, any drive letter or profile path, any read of a real key, or any other write or deletion: UNEXPECTED, and STOP.
* C3. Copy `authoring_kit\` into the project. Fix only the kit's own bugs; log each fix with file:line.
* C4. Run `python authoring_kit\tests\run_kit_tests.py` under Windows Python. The kit reports 9 of 9 scripts and 496 checks on Linux; report any difference.
* C5. Run `python authoring_kit\python\compat_check.py --root .` on the real engine. Report each pattern as `AVAILABLE NATIVE`, `AVAILABLE GENERIC` or `UNAVAILABLE missing <term>`, each capability and the term it resolved to, and every missing native relation as a PROPOSED ADDITION with a recommendation. Fix wrong candidate names only in `authoring_kit\data\capability_map.json`. Do not add schema fields.
* C6. Parser test (most important). Run the real `check_case.py` on CASE-FIX-01 to 03 and on every broken variant, and feed each output to `repair_builder.parse_engine_output` with the rule IDs `compat_check` found. Each BRK variant must yield exactly its own rule ID and path (BRK-FP-05 may also trip FP-08, as recorded in Entry 012). A variant the schema rejects before any rule runs may yield the generic `CHK-1`; record which ones. Clean fixtures must yield nothing. Any other mismatch: fix the kit's parser or `engine_output` settings, or STOP if the fix is not small.
* C7. **[R3]** Placeholder tolerance. Run `python authoring_kit\python\placeholder_probe.py --root . --case <fixture> --skin <skin>` on CASE-FIX-01 and CASE-FIX-03, report the rules it lists, then run it once with `--write`. Confirm in the code and with one fake-agent run that tolerance applies only at S2 and the S3 gate, and that S4 and finish run the full check.
* C8. **[R3]** Confinement. The kit creates stage folders outside the workspace and deletes each one when its unit is accepted, so only the current unit's folder is ever on disk. Prove it on Windows with one fake-agent run (`--stage-root` left empty): no folder named `stages` under the workspace, and only the marker plus the current unit under the stage root. Then review, without a live run, how `author_run.py` launches `claude -p`, and read `claude --help` (or the current documentation) for the flags that limit tools, file access and permission mode. Cite what you read. State plainly whether a live S3 agent, as configured, could still read other paths on disk (the workspace, the vault) by absolute path. If it could, record it as an OPEN risk with the flag or setting that would close it, and do not wire a live path.
* C9. **[R3]** Model and effort. The kit fills `{model}` and `{effort}` per stage from `stage_plan.json`, falling back to `agent.default_model` and `agent.default_effort`. Set those defaults from `taste\rules\authoring.json`. Run `python authoring_kit\python\kit_run.py estimate --documents 6` and `--documents 12` and report both results against `limits.turns`.
* C10. **[R3]** Usage-limit pause. The kit pauses (exit 5) instead of failing when the agent's exit code or output matches `agent.pause`, and `next` restarts the same unit. Confirm the real signals Claude Code gives when a plan limit is reached, from its documentation or `--help`; cite them; set `agent.pause` accordingly; mark any signal you could not confirm UNVERIFIED in the build log.
* C11. Wire the kit into `taste\tools\author_run.py` behind `--kit`. The runner, not the kit, keeps re-running `check_case`, `check_conformance` and `pack`, cleaning up its temporary workspace, and being the only writer to the vault. Set `agent.family` to the authoring model's family and leave `audit_agent` for the audit. Enable pack and export in `kit_config.json` only after C6 and C7 pass. Append a pointer to the kit in `engine\README_AUTHORING_FOR_OPUS.md`.
* C12. Real-schema fake scenario. The kit's test scenario uses its nonsense fake engine, not the real schema. Write `authoring_kit\tests\fixtures\real_scenario\` from CASE-FIX-03: its case with prose turned into placeholders (S2), its original nonsense prose as fills (S3, S4), and a hand-written nonsense `bible.json` and `clue_plan.json` that match it and pass the kit's checks. Nonsense only. **[R3]** This step waits until GATE B is merged into `build/mvp` and then into `build/mvp-c` (see `01_ORCHESTRATION.md`), because the compound-query rule changes search. Then run the whole chain with the fake agent: kit, runner, pack, `export_desk`, `client\data\current.case.js`. Report counts and rule results. Then delete `current.case.js` to restore the default fixture.
* C13. **[R3]** Blind-audit dry run. Point `kit_config.json` → `audit.questions_path` (and `audit.cite_map` if the bundle re-keys clues) at the real player bundle shape. Run `kit_run.py audit` on the C12 workspace with the packed bundle, using the fake agent as the audit agent and two different test family names. Show that it prints only verdicts, numbers and IDs, and that the shortcut stage folder contains no records.
* GATE C: readout passes (report the counts); the kit's tests pass, including any new ones; the parser test passes; the full fake chain exports a case that round-trips with 0 missing fields; no stage folder is created inside a workspace; the audit dry run prints IDs and numbers only. Commit by explicit path and tag `gate-C`. Then the Auditor reviews before agent 1 merges.

### Phase D: merge and hand over (agent 1)

* D1. **[R3]** After the Auditor clears each gate: merge `build/mvp-b` into `build/mvp` (merge commit, no rebase); after GATE C, merge `build/mvp-c` into `build/mvp`. Run the full readout, Desk tests, taste readout and kit tests on `build/mvp`.
* D2. Print the PowerShell commands Aetherius runs to play the exported CASE-FIX-03 in Firefox, and to return to the default.
* D3. Scope check: `git diff --name-only gate-A..build/mvp` must list only files allowed in phases B and C. Report any file outside them.
* D4. Write the build log summary, update `docs\CODEBASE_STATE.md` by appending, and draft a Living Log entry (check the newest number first; show the text, do not post it). Remove the worktrees with `git worktree remove`.
* D5. Report in under 40 lines and end with a VERDICT line (`SAFE TO MERGE` or `HOLD`, with the single reason).

## 5. STOP conditions (stop, write the log, report, wait)

1. Any gate fails twice in a row with the same rule or test.
2. A change is needed in an off-limits file, or in a file outside your phase's scope.
3. The security scan finds anything UNEXPECTED (C2).
4. BACKUP_PATH is blank, D: or H:.
5. Anything would touch the vault, a path under `cases\` other than fixtures, a push, a deletion not listed in rule 5, or a system setting.
6. A command is denied, or an approval prompt appears for something this plan does not cover. Do not work around it.
7. You are about to spend plan credits: any live agent, image or authoring run.
8. The cloned kit's commit does not equal KIT_COMMIT (C1).
9. **[R3]** A SEALED or SPOILERS folder is found inside the project folder or a worktree.
10. **[R3]** Two agents need the same file, or a merge conflicts in logic (not just in a log or status file).

## 6. After this plan (NOT part of it; each needs Aetherius's word)

1. A second model reviews `build/mvp` read-only, and the readout runs in a fresh clone.
2. The tiny live probe: one cheap Claude Code invocation through the kit on a nonsense task, with a canary file placed somewhere the agent must not read, to measure real credit cost and prove confinement.
3. The first real case, only when Aetherius types `--go`: one aha pattern, a modest brief, authored by Claude through Claude Code (Mode A).
4. **[R3]** The cross-family blind audit of that case (S7): a Gemini agent in Antigravity (Argon) runs the shortcut probe and the cold solve from the player bundle only, following `AGENT_PLAYBOOK.md`. The kit prints verdicts and IDs only. Then Aetherius plays it cold and fills in the feedback form.
5. Applying the look (freeze to 3.0.0 first). The semantic audit design (the kit's `claims.json` is its input). The play layer.
