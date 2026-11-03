ROLE: Kit v4 Installer. One agent, one lane. You install the authoring kit's media layer into the project and prove it works with a fake agent. You never write a case and never spend credits.

SETUP: git -C "D:\Project Recess" worktree add "D:\pmm-worktrees\kitv4" -b build/kit-v4 master. Work only in D:\pmm-worktrees\kitv4\Project Mystery Machine.

HARD RULES
- Never touch the main checkout D:\Project Recess\Project Mystery Machine: an authoring run may be using it.
- Never open the vault, cases\ (fixtures excepted), anything SEALED or SPOILERS, %TEMP%\mm_kit_stages_*, %TEMP%\pmm_author_*, or %USERPROFILE%\.mm_secrets\.
- No push. No network except one git clone from GitHub (K1). No live (paid) agent call.
- Commit by explicit path only, on build/kit-v4. Do not merge.

READ FIRST: authoring_kit\docs\INTEGRATION.md and docs\reports\2026-11-02_build-log_live-wright.md in your worktree.

K0. Run the readout, the Desk tests, the taste readout and the kit tests; record the counts (expect kit tests 9 of 9 scripts, 502 checks).

K1. Kit update. git clone --branch claude/eager-davinci-qgiihc https://github.com/ClaysAnatomy/hello-world incoming\kit_v4 (incoming\ is gitignored). Note the clone's HEAD commit and confirm it contains commit 71d03b9 ("Kit: mixed-media layer"). Make the patch, leaving out the one file that has local changes:
  git -C incoming\kit_v4 diff 015f9ac HEAD -- authoring_kit ":(exclude)authoring_kit/data/capability_map.json" > incoming\kit_v4.patch
From D:\Project Recess, run git apply --check --directory="Project Mystery Machine" on it, then apply it. If any hunk fails, STOP and report the file and hunk. It must not touch kit_config.json, repair_builder.py, kitlib.py or capability_map.json: local changes stay.

K2. Capability names. In authoring_kit\data\capability_map.json, add each of these candidate names to its capability's candidates list if it is not already there; change nothing else:
  CAP-03 masks_option_ids; CAP-04 aha_moments, aha_patterns, aha_id; CAP-18 AHA_ALIBI_INVERSION, AHA_MOTIVE_INVERSION; CAP-19 AHA_IDENTITY_COLLAPSE; CAP-20 AHA_IDENTITY_FISSION; CAP-21 AHA_TEMPORAL_SHIFT; CAP-22 AHA_SPATIAL_SHIFT; CAP-23 AHA_NEGATIVE_CLUE; CAP-24 AHA_EPISTEMIC_TRAP; CAP-25 AHA_TARGET_SWAP; CAP-26 teaches_rule_ids; CAP-28 fragment_quarters, fragment.
Then check that authoring_kit\data\patterns.json → each pattern's engine_aha exists in engine\schemas\vocabulary.json; list any that do not, and if the vocabulary describes its AHA_* terms, say whether each mapping fits the pattern's mechanism.

K3. Tests. Run python authoring_kit\tests\run_kit_tests.py: expect 10 of 10 scripts and 597 checks; report any difference with the failing check names. Run python authoring_kit\python\compat_check.py --root . and report the available, NATIVE and GENERIC counts (16 of 16 expected; up to 16 NATIVE).

K4. Media manifest. In taste\tools\author_run.py, wherever the runner copies the kit's finished files (case, skin, claims) into the vault and the player bundle, also copy media_manifest.json when it exists. Change nothing else in the runner.

K5. Fake chain. Repeat the Live Wright's zero-spend fake chain: author_run.py --brief latest --kit --go with the kit's fake agent through the KIT_CONFIG_OVERRIDE mechanism, on a nonsense fixture brief from taste\fixtures\. It must pass end to end. Report the engine rules, conformance checks and whether media_manifest.json appeared (it appears only when the plan declares media; a fixture without media is fine). Delete the fake workspace afterwards.

K6. Commit by explicit path on build/kit-v4: the patched kit files, capability_map.json, author_run.py and docs\reports\2026-11-02_build-log_kit-v4.md. Do not merge.

REPORT (under 25 lines): K0 and K3 counts; files the patch changed; candidates added in K2; the engine_aha check; compat counts; the K4 change; the K5 result; anything OPEN. Last line: KIT V4 READY or KIT V4 BLOCKED <reason>.
