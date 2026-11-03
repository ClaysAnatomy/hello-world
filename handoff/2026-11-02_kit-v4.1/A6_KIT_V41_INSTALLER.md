ROLE: Kit v4.1 Installer. One agent, one lane. You install the fix for the first real run's S1 failure into the authoring kit and prove it with the fake agent. You never write a case and never spend credits.

WHY: The first real run (BRIEF-20261102-163208) failed with KT-BI-01 at "$". S1 timed out after 30 minutes with no file; the repair wrote a 261-line bible that stopped mid-object and ran out of turns. v4.1 has S1 write the bible as five small part files, names any broken file and its line, gives S1 and repairs realistic turn caps, and logs each agent run's result word (success, error_max_turns, timeout) without any text.

SETUP: git -C "D:\Project Recess" worktree add "D:\pmm-worktrees\kitv41" -b build/kit-v41 master. Work only in D:\pmm-worktrees\kitv41\Project Mystery Machine.

HARD RULES
- Never change anything in the main checkout D:\Project Recess\Project Mystery Machine.
- Never open the vault, cases\ (fixtures excepted), anything SEALED or SPOILERS, %TEMP%\mm_kit_stages_*, %TEMP%\pmm_author_*, or %USERPROFILE%\.mm_secrets\.
- No push. No network except one git clone from GitHub (K1). No live (paid) agent call.
- Never edit kit_config.json or capability_map.json: v4.1 needs no change to either.
- Commit by explicit path only, on build/kit-v41. Do not merge.

K0. Baseline. Confirm the kit in your worktree already has the v4 media layer: authoring_kit\python\media.py and authoring_kit\docs\MEDIA.md exist. If either is missing, STOP: KIT V41 BLOCKED v4 not installed. Run python authoring_kit\tests\run_kit_tests.py and record the counts (expect 10 of 10 scripts, 597 checks). Record git diff --stat master -- authoring_kit (should be empty) and list which of authoring_kit\python\kitlib.py and authoring_kit\python\repair_builder.py differ from the kit's published v4 (commit eacd25d of the clone in K1): those are local edits to keep.

K1. Fetch. git clone --branch claude/zealous-pasteur-g9zvdz https://github.com/ClaysAnatomy/hello-world incoming\kit_v41 (incoming\ is gitignored). Note the clone's HEAD and confirm its log contains "Kit v4.1: write the S1 bible in five parts". Make the code patch, leaving out every data JSON file (K3 handles those):
  git -C incoming\kit_v41 diff eacd25d HEAD -- authoring_kit ":(exclude)authoring_kit/data/*.json" > incoming\kit_v41.patch

K2. Apply the code patch. From D:\pmm-worktrees\kitv41 run git apply --check --directory="Project Mystery Machine" incoming\kit_v41.patch (adjust the patch path to where you saved it). If it passes, apply it. If hunks fail ONLY in kitlib.py or repair_builder.py (files with local edits), apply the rest with --exclude for those files, then add their v4.1 changes by hand, keeping the local edits:
  - kitlib.py: load_json opens with encoding "utf-8-sig"; the new read_output function after it; schema_errors names missing (required) and unexpected (additionalProperties false) fields.
  - repair_builder.py: failures_table's "Where" column shows file, line and path when a finding has "file".
  Take the exact code from incoming\kit_v41. If any other file fails, STOP and report the file and hunk.

K3. Data files. From the project folder (D:\pmm-worktrees\kitv41\Project Mystery Machine):
  python incoming\kit_v41\handoff\2026-11-02_kit-v4.1\apply_data_changes.py --check
  python incoming\kit_v41\handoff\2026-11-02_kit-v4.1\apply_data_changes.py
(adjust the script path to the clone). It edits stage_plan.json, check_catalog.json, limits.json and messages.json key by key and keeps local values such as limits.json → tolerated_engine_rules. Run it a second time: it must print "CHANGED nothing (already applied)". Confirm tolerated_engine_rules is unchanged from master.

K4. Tests. python authoring_kit\tests\run_kit_tests.py: expect 10 of 10 scripts and 645 checks; report any difference with the failing check names. python authoring_kit\python\compat_check.py --root .: counts must match K0's world (16 of 16 expected).

K5. Fake chain. Repeat the zero-spend fake chain from the v4 install: author_run.py --brief latest --kit --go with the kit's fake agent through the KIT_CONFIG_OVERRIDE mechanism, on a nonsense fixture brief from taste\fixtures\. The fake agent's S1 outputs must now be the five files under bible_parts\ (see authoring_kit\tests\fixtures\scenario.py → bible_parts): if the runner's fake setup writes a single bible.json instead, it still passes through the kit's fallback; note which one ran. It must pass end to end. Confirm the workspace's checkpoints\agent_log.json exists and holds only unit, exit, result, turns, seconds, denials and cost_usd keys (read the key names only). Delete the fake workspace afterwards.

K6. Runner note. If taste\tools\author_run.py prints a cost total from the kit, check whether it reads checkpoints\state.json → budget. If so, also print the kit's line "BUDGET cost not reported for N agent run(s)" when state.json → budget.cost_unknown is above 0 (only when the agent reports usage JSON). Change nothing else in the runner. If the runner gets its total some other way, change nothing and say how.

K7. Commit by explicit path on build/kit-v41: the patched kit files, the four data JSON files, author_run.py if K6 changed it, and docs\reports\2026-11-02_build-log_kit-v41.md. Do not merge.

REPORT (under 25 lines): K0 and K4 counts; which local edits were kept and how (K2); the K3 output both times; compat counts; the K5 result and which S1 shape ran; the K6 finding; anything OPEN. Last line: KIT V41 READY or KIT V41 BLOCKED <reason>.

AFTER MERGE (for the human, not the installer): rerun the same real brief. A healthy S1 prints AGENT S1 exit 0 with no result line, then CHECK S1 PASS. If it fails, the lines now say which part, which line, and the result word (error_max_turns means the turn cap; "timed out after 30 minutes" with no files means the agent never wrote: look at the model's output limit next).
