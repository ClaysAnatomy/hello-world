# Integration

The kit was written without access to the project. Everything below is where it meets the real code. The kit changes no existing file.

## Integration points

1. **Workspace and stage root.** Pass `--ws <vault_dir>\<case_id>`, with `vault_dir` from `taste\rules\authoring.json`. Checkpoints land in `<vault_dir>\<case_id>\checkpoints\` (Entry 024). Stage folders, where agents work, go to `--stage-root` or a new folder under `%TEMP%`, never inside the workspace (Entry 014: the authoring model is never given the vault path). Each stage folder is deleted when its unit is accepted; finish deletes the stage root. Deletion only ever happens inside a folder carrying the `.mm_kit_stage_root` marker.
2. **Brief.** Pass the taste layer's author brief with `--brief`. Anything from one word to a full brief works; S1 treats it as anchors.
3. **Engine paths.** `data\kit_config.json` → `engine`. Defaults follow the dev log.
4. **Engine checks.** `engine_checks` in `kit_config.json`. `check_case.py <case> --skin <skin>` is enabled. `pack.py` and `export_desk.py` are present but disabled until their real arguments are filled in.
5. **Capability names.** `data\capability_map.json` holds candidate terms for 28 capabilities, including the research's relation names (INVERTS-POLARITY, SHIFTS-WINDOW, PRESUPPOSES and the rest). `compat_check.py` confirms them. A pattern whose native relation is missing can still run GENERIC through REFRAMES, MASKS or CONTRADICTS; a PROPOSED ADDITION to the schema is the engine owner's decision, not the kit's.
6. **Prose-dependent rules.** Run `placeholder_probe.py` on CASE-FIX-01 and CASE-FIX-03. With `--write`, it fills `limits.json` → `tolerated_engine_rules.S2` and `.S3_GATE`. S4 and finish always run the full check.
7. **Mode A agent.** Fill `agent.argv`. Tokens: `{prompt_file}`, `{stage_dir}`, `{max_turns}`, `{model}`, `{effort}`, `{python}`. An argument whose token fills empty is dropped whole, so write optional flags as one argument (`--model={model}`). Per-stage model and effort live in `stage_plan.json`; blank means `agent.default_model` and `agent.default_effort`. Variables ending `_API_KEY` or `_AUTH_TOKEN` are removed from the authoring agent's environment. For the Claude Code plan route the shape would be along the lines of `["claude", "-p", "--output-format", "json", "--max-turns", "{max_turns}", "--model={model}"]` with `usage_from_stdout_json: true`; check every flag against `claude --help` before use.
8. **Usage-limit pause.** `agent.pause` lists exit codes and output patterns that mean "stopped by a plan or rate limit". They are UNVERIFIED: confirm the real signals from the agent's documentation. A matched stop with missing outputs pauses the run (exit 5); `next` restarts the same unit without using a repair round.
9. **Blind audit.** Set `agent.family` and `audit_agent.family` to two different model families, and `audit_agent.argv` for Mode A. `audit.questions_path` says where the questions sit in the player bundle. If the exporter re-keys clue IDs to record references, provide `audit.cite_map` (a JSON map from reference to clue ID, stored in the sealed workspace). The audit agent keeps its own keys: only `_AUTH_TOKEN` variables are stripped for it by default.
10. **Taste.** Entry 024 says to extend `store.py` and `learn.py` rather than add `feedback_ingest.py`. `taste_bridge.apply(profile, answers, seeds)` is the pure function for `learn.py` to call.
11. **State files.** `authoring_kit\state\ledger.json` (salted hashes only) and `taste_profile.json`. `authoring_kit\.gitignore` already ignores `state/`.
12. **The existing runner.** `taste\tools\author_run.py` keeps its own route. Behind `--kit`, it calls `kit_run.py` with the same workspace, then runs its own checks, pack and export as the only writer to the vault.

## Task list for the local builder

1. `python -m pip install jsonschema`, then run `python authoring_kit\tests\run_kit_tests.py` on Windows (expect 9 of 9, 502 checks).
2. Run `compat_check.py --root .`; fix any wrong candidate names in `capability_map.json`.
3. Run `placeholder_probe.py` on CASE-FIX-01 and CASE-FIX-03 with `--write`.
4. Confirm the `engine` paths, and that the ID grammar in the authoring contract fits `limits.json` → `ids`.
5. Fill in and enable the `pack.py` and `export_desk.py` entries with their real arguments.
6. Feed the real `check_case.py` output for every fixture and broken variant through `repair_builder.parse_engine_output`; each variant must yield its own rule ID and path.
7. Wire `--kit` into `author_run.py`; fill `agent.argv`, the families and the pause signals from the agent's real documentation.
8. Build a real-schema nonsense scenario from CASE-FIX-03 and run the full fake-agent chain through pack and export.
9. Wire `taste_bridge.apply` into `learn.py` (Entry 024), or keep the kit-local profile.
10. After the first real run, set `limits.json` → `turns` from measurements and tune the voice rules against the prose.
