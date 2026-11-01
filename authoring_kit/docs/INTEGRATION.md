# Integration

The kit was written without access to the project. Everything below is where it meets the real code. The kit changes no existing file.

## Integration points

1. **Workspace.** Pass `--ws <vault_dir>\<case_id>`, with `vault_dir` from `taste\rules\authoring.json`. Checkpoints then land in `<vault_dir>\<case_id>\checkpoints\`, as Entry 024 requires. The kit itself never knows a vault path.
2. **Brief.** Pass the taste layer's author brief with `--brief`. Anything from one word to a full brief works; S1 treats it as anchors.
3. **Engine paths.** `data\kit_config.json` → `engine`. Defaults follow the dev log (`engine\schemas\case*.json`, `engine\rules\*.json`, `engine\contract\bundle_contract.json`, `engine\README_AUTHORING_FOR_OPUS.md`, CASE-FIX-01 and SKIN-FIX_A).
4. **Engine checks.** `engine_checks` in `kit_config.json`. `check_case.py <case> --skin <skin>` is enabled. `pack.py` and `export_desk.py` are present but disabled, because their exact arguments are not known here.
5. **Capability names.** `data\capability_map.json` lists candidate engine terms per capability. `compat_check.py` confirms them against the real schema and vocabulary.
6. **Prose-dependent rules.** S2 writes placeholders in every prose field. If a real rule needs real prose (for example a search rule), list its ID in `limits.json` → `tolerated_engine_rules.S2` (and `S3_GATE` if needed). It is still enforced at S4 and at finish.
7. **Mode A agent.** Fill `agent.argv` in `kit_config.json`. Tokens: `{prompt_file}`, `{stage_dir}`, `{max_turns}`, `{python}`. With `"stdin": "prompt"` the prompt is also sent on stdin. Variables ending `_API_KEY` or `_AUTH_TOKEN` are removed from the child's environment. For the Claude Code plan route the shape would be along the lines of `["claude", "-p", "--output-format", "json", "--max-turns", "{max_turns}"]` with `usage_from_stdout_json: true`; check the flags against the current CLI before use. Any other agent works the same way.
8. **Taste.** Entry 024 says to extend `store.py` and `learn.py` rather than add `feedback_ingest.py`. `taste_bridge.apply(profile, answers, seeds)` is the pure function for `learn.py` to call. Its CLI writes `authoring_kit\state\taste_profile.json`, which `seed_sampler` reads.
9. **State files.** `authoring_kit\state\ledger.json` (salted hashes only) and `taste_profile.json`. Add `authoring_kit/state/` to `.gitignore`.
10. **The existing runner.** `taste\tools\author_run.py` keeps its own route. A thin wrapper (or a new flag) can call `kit_run.py` with the same workspace and then the runner's existing checks.

## Task list for the local builder

1. `python -m pip install jsonschema`, then run `python authoring_kit\tests\run_kit_tests.py` on Windows (expect 8 of 8).
2. Run `python authoring_kit\python\compat_check.py --root .` and fix any wrong candidate names in `capability_map.json`.
3. Confirm the `engine` paths in `kit_config.json`, and that the ID grammar in the authoring contract fits `limits.json` → `ids`.
4. Fill in and enable the `pack.py` and `export_desk.py` entries, with their real arguments.
5. Do a Mode B dry run to S2 with any agent on a nonsense brief; note which rules fail only because of placeholders, and list them in `tolerated_engine_rules`.
6. Add `authoring_kit/state/` to `.gitignore`.
7. Wire `taste_bridge.apply` into `learn.py` (Entry 024), or keep the kit-local profile.
8. Fill `agent.argv` for Mode A and confirm the stripped-variable rule matches `strip_api_key_env`.
9. Measure one real run's turns per stage, then set `limits.json` → `turns` from measurements.
10. Read one finished `claims.json` to confirm it fits the planned semantic audit (Tier C).
