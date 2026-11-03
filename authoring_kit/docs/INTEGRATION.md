# Integration

The kit was written without access to the project. Everything below is where it meets the real code. The kit changes no existing file.

## Integration points

1. **Workspace and stage root.** Pass `--ws <vault_dir>\<case_id>`, with `vault_dir` from `taste\rules\authoring.json`. Checkpoints land in `<vault_dir>\<case_id>\checkpoints\` (Entry 024). Stage folders, where agents work, go to `--stage-root` or a new folder under `%TEMP%`, never inside the workspace (Entry 014: the authoring model is never given the vault path). Each stage folder is deleted when its unit is accepted; finish deletes the stage root. Deletion only ever happens inside a folder carrying the `.mm_kit_stage_root` marker.
2. **Brief.** Pass the taste layer's author brief with `--brief`. Anything from one word to a full brief works; S1 treats it as anchors.
3. **Engine paths.** `data\kit_config.json` → `engine`. Defaults follow the dev log.
4. **Engine checks.** `engine_checks` in `kit_config.json`. `check_case.py <case> --skin <skin>` is enabled. `pack.py` and `export_desk.py` are present but disabled until their real arguments are filled in.
5. **Capability names.** `data\capability_map.json` holds candidate terms for 28 capabilities, including the research's relation names (INVERTS-POLARITY, SHIFTS-WINDOW, PRESUPPOSES and the rest). `compat_check.py` confirms them. A pattern whose native relation is missing can still run GENERIC through REFRAMES, MASKS or CONTRADICTS; a PROPOSED ADDITION to the schema is the engine owner's decision, not the kit's.
6. **Prose-dependent rules.** Run `placeholder_probe.py` on CASE-FIX-01 and CASE-FIX-03. With `--write`, it fills `limits.json` → `tolerated_engine_rules.S2` and `.S3_GATE`. S4 and finish always run the full check.
7. **Mode A agent.** Fill `agent.argv`. Tokens: `{prompt_file}`, `{stage_dir}`, `{max_turns}`, `{model}`, `{effort}`, `{python}`. An argument whose token fills empty is dropped whole, so write optional flags as one argument (`--model={model}`). Per-stage model and effort live in `stage_plan.json`; blank means `agent.default_model` and `agent.default_effort`. Variables ending `_API_KEY` or `_AUTH_TOKEN` are removed from the authoring agent's environment. For the Claude Code plan route the shape would be along the lines of `["claude", "-p", "--output-format", "json", "--max-turns", "{max_turns}", "--model={model}", "--permission-mode", "acceptEdits"]` with `usage_from_stdout_json: true`. Without a permission mode a headless agent cannot write its outputs. Check every flag against `claude --help` before use (`--max-turns` is accepted though not listed there). From the final JSON the kit keeps only numbers, the result word (`subtype`: success, error_max_turns and so on) and the count of `permission_denials`; it writes them to `checkpoints\agent_log.json` and prints the word when a run does not succeed. No other key needs adding to `kit_config.json` for this.
8. **Usage-limit pause.** `agent.pause` lists exit codes and output patterns that mean "stopped by a plan or rate limit". They are UNVERIFIED: confirm the real signals from the agent's documentation. A matched stop with missing outputs pauses the run (exit 5); `next` restarts the same unit without using a repair round.
9. **Blind audit.** Set `agent.family` and `audit_agent.family` to two different model families, and `audit_agent.argv` for Mode A. `audit.questions_path` says where the questions sit in the player bundle. If the exporter re-keys clue IDs to record references, provide `audit.cite_map` (a JSON map from reference to clue ID, stored in the sealed workspace). The audit agent keeps its own keys: only `_AUTH_TOKEN` variables are stripped for it by default.
10. **Taste.** Entry 024 says to extend `store.py` and `learn.py` rather than add `feedback_ingest.py`. `taste_bridge.apply(profile, answers, seeds)` is the pure function for `learn.py` to call.
11. **Media.** When a plan dresses documents as artifacts, `finish` writes `media_manifest.json` (player-safe) next to the case, and `checkpoints/media_registry.json` stays sealed. `author_run.py` should carry `media_manifest.json` into the vault and the player bundle alongside the case. The Desk renders artifacts from it; the image pipeline reads its `plates`. See `docs/MEDIA.md`.
12. **Agent runs that time out.** A run that hits `limits.json` → `timeouts.stage_minutes` reports no turns or cost. The kit charges the full turn cap, prints that the cost is unknown, and `status` counts such runs; a runner that totals cost from the kit ("Total cost reported") under-reports by those runs.
13. **State files.** `authoring_kit\state\ledger.json` (salted hashes only) and `taste_profile.json`. `authoring_kit\.gitignore` already ignores `state/`.
14. **The existing runner.** `taste\tools\author_run.py` keeps its own route. Behind `--kit`, it calls `kit_run.py` with the same workspace, then runs its own checks, pack and export as the only writer to the vault.

## Task list for the local builder

1. `python -m pip install jsonschema`, then run `python authoring_kit\tests\run_kit_tests.py` on Windows (expect 10 of 10, 645 checks).
2. Run `compat_check.py --root .`; fix any wrong candidate names in `capability_map.json`.
3. Run `placeholder_probe.py` on CASE-FIX-01 and CASE-FIX-03 with `--write`.
4. Confirm the `engine` paths, and that the ID grammar in the authoring contract fits `limits.json` → `ids`.
5. Fill in and enable the `pack.py` and `export_desk.py` entries with their real arguments.
6. Feed the real `check_case.py` output for every fixture and broken variant through `repair_builder.parse_engine_output`; each variant must yield its own rule ID and path.
7. Wire `--kit` into `author_run.py`; fill `agent.argv`, the families and the pause signals from the agent's real documentation.
8. Build a real-schema nonsense scenario from CASE-FIX-03 and run the full fake-agent chain through pack and export.
9. Wire `taste_bridge.apply` into `learn.py` (Entry 024), or keep the kit-local profile.
10. After the first real run, set `limits.json` → `turns` from measurements and tune the voice rules against the prose. (Done once for S1 and repairs after the 2026-11-02 run; `checkpoints\agent_log.json` now records turns, seconds and the result word per run, so later runs can be measured without opening anything sealed.)

## Kit v4.2: never pay twice

- **S2 is two stages.** S2A writes `clue_plan.json`; S2B writes `case.json` and `skin.json` from the accepted plan. Engine checks still run under the label `S2`, so `kit_config.json` and `tolerated_engine_rules.S2` are unchanged.
- **Inputs are inline.** Every stage prompt carries its inputs in full (JSON minified), so agents spend no turns reading files.
- **Saved attempts.** Every agent output is copied to `<ws>\checkpoints\attempts\<unit>\` the moment the agent returns, before any check.
- **Recovery.** If a run is interrupted after an agent wrote its files, `next` checks those files instead of paying for the unit again.
- **`kit_run.py resume --ws <ws>`** reopens an aborted, stopped or interrupted run: accepted units stay, repair rounds reset, and the budget starts a new pass (`budget.passes` keeps earlier spend).
- **`kit_run.py cleanup --hours 12`** deletes old marked stage roots in the temp folder, unopened.
- **`kit_run.py preflight --root .`** checks the set-up before spending: jsonschema, `--restricted`, the `--settings` file, usage reporting, engine files, stages and prompts, caps, and stale stage roots.
- **Budget.**
  - The run cap is $15.00.
  - Each repaired unit has its own turn pool (`repair_target_caps`).
  - `reported_multiplier` scales reported cost to what the provider charges.
  - A run that reports no cost is charged a share of its stage cap.
- **The runner must:**
  - keep the workspace on every exit, including Ctrl+C, by copying it to the vault before any purge;
  - offer `--resume <CASE_ID>` instead of starting a new case;
  - never restart authoring from scratch as a "pass";
  - run `preflight` before `init`, and `cleanup` at start;
  - use the kit's caps rather than its own lower ones.
