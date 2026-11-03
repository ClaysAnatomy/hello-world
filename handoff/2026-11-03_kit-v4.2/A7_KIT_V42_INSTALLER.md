ROLE: Kit v4.2 Installer. One agent, one lane. You install kit v4.2 (never pay twice), make the runner keep and resume paid work, and check whether the last real case can be salvaged. You never write a case and never spend credits.

WHY: The second real run (CASE-20261102-1850) passed S1, then S2 timed out writing three large files in one go; its repair could not start because all repairs shared one turn pool; the runner then ended the case. About $5 was spent, and the runner would have started a brand-new case (new story, paid again) next time. v4.2 splits S2 into S2A and S2B, puts inputs inline, saves every output before checking it, and adds resume, cleanup and preflight. The runner must stop throwing away paid work.

SETUP: git -C "D:\Project Recess" worktree add "D:\pmm-worktrees\kitv42" -b build/kit-v42 master. Work only in D:\pmm-worktrees\kitv42\Project Mystery Machine.

HARD RULES
- Never change anything in the main checkout D:\Project Recess\Project Mystery Machine.
- Never open, print or copy the contents of anything in the vault, cases\ (fixtures excepted), anything SEALED or SPOILERS, %TEMP%\mm_kit_stages_*, %TEMP%\pmm_author_*, or %USERPROFILE%\.mm_secrets\. In K6 you may use Test-Path on three named files and nothing else.
- No push. No network except one git clone from GitHub (K1). No live (paid) agent call.
- Never edit kit_config.json or capability_map.json.
- Commit by explicit path only, on build/kit-v42. Do not merge.

K0. Baseline. Run python authoring_kit\tests\run_kit_tests.py: expect 10 of 10 scripts, 645 checks (v4.1). Record the counts.

K1. Fetch. git clone --branch claude/eager-davinci-qgiihc https://github.com/ClaysAnatomy/hello-world incoming\kit_v42 (incoming\ is gitignored). Confirm its log contains 404233a "Kit v4.2: never pay twice". Make the code patch, leaving out the data JSON (K2 handles it):
  git -C incoming\kit_v42 diff 5a041b8 404233a -- authoring_kit ":(exclude)authoring_kit/data/*.json" > incoming\kit_v42.patch
From D:\pmm-worktrees\kitv42, run git apply --check --directory="Project Mystery Machine" on it, then apply it. It renames prompts\S2_clue_plan.md to S2A_doc_plan.md and adds S2B_engine_files.md, test_resume.py and the new commands. If any hunk fails, STOP and report the file and hunk.

K2. Data. From the project folder:
  python incoming\kit_v42\handoff\2026-11-03_kit-v4.2\apply_data_changes.py --from incoming\kit_v42\authoring_kit\data --check
  python incoming\kit_v42\handoff\2026-11-03_kit-v4.2\apply_data_changes.py --from incoming\kit_v42\authoring_kit\data
Run it a third time: it must print "CHANGED nothing (already applied)". Confirm limits.json → tolerated_engine_rules is unchanged from master.

K3. Tests. run_kit_tests.py: expect 11 of 11 scripts and 700 checks; report any difference with the failing check names. compat_check.py --root .: 16 of 16. python authoring_kit\python\kit_run.py preflight --root .: report every PREFLIGHT line (PF-08 WARN is fine: it only means old stage folders exist).

K4. Runner. In taste\tools\author_run.py (and taste\rules\authoring.json for limits), make these changes and nothing else:
  R1 Keep paid work on every exit. On success, failure, exception and Ctrl+C (KeyboardInterrupt), copy the whole kit workspace, including checkpoints\, into the vault attempt folder BEFORE deleting any temp folder. If the copy fails, do not delete the temp workspace; print its path.
  R2 Resume. Add --resume <CASE_ID>. Find that case's kept attempt in the vault through the runner's own path logic, copy it to a fresh %TEMP%\pmm_author_* workspace, run kit_run.py resume --ws <workspace>, then continue exactly as a normal run (next --all, finish, the runner's checks, pack, export, publish). Never sample new seeds or a new case ID when resuming. If checkpoints\state.json is missing from the attempt (Test-Path), print "RESUME not possible: no saved kit state" and stop.
  R3 No from-scratch passes. After a failure the runner never re-authors the case with new seeds. If it has a passes setting, set it to 1. On failure it prints the exact resume command for that case ID.
  R4 Limits. The runner's own caps match the kit: $15.00 per case, 240 minutes wall clock; the header prints the kit's limits.json values.
  R5 Before init (and before resume): run kit_run.py cleanup --hours 12, then kit_run.py preflight --root .; if preflight prints PREFLIGHT FAIL, stop before spending and print the lines.
  R6 At the end of every run, print the spend from the workspace's checkpoints\state.json → budget (this pass, and the sum of budget.passes), as numbers only.

K5. Prove it with the fake agent (zero spend), through KIT_CONFIG_OVERRIDE, on a nonsense fixture brief from taste\fixtures\:
  a) A normal fake run passes end to end.
  b) An interrupted fake run: make the fake run stop after S2A (for example, a fake S2B output that fails the same check twice so the kit aborts). Confirm the attempt was kept in a scratch vault folder you create for the test (never the real vault). Then run --resume on that case ID with a good fake S2B: it must finish, and the fake agent's _calls.json must show S1 and S2A were not called again.
  c) Ctrl+C: simulate a KeyboardInterrupt during the kit step and confirm R1 copied the workspace before cleanup.
  Delete all fake workspaces and the scratch vault afterwards.

K6. Salvage check for CASE-20261102-1850. Using only Test-Path, through the runner's own vault path logic, report YES or NO for each of these inside that case's kept attempt: checkpoints\state.json, checkpoints\bible.json, checkpoints\seeds.json. Open nothing and list nothing.

K7. Commit by explicit path on build/kit-v42: the patched kit files, the three data JSON files, author_run.py, authoring.json if R4 changed it, and docs\reports\2026-11-03_build-log_kit-v42.md. Do not merge.

REPORT (under 30 lines): K0 and K3 counts; files the patch changed; the K2 output; the PREFLIGHT lines; R1 to R6, one line each; the K5 results a, b and c; the K6 answers; anything OPEN. Last line: KIT V42 READY or KIT V42 BLOCKED <reason>.

AFTER MERGE (for the human): if K6 said YES three times, resume the arctic case instead of starting a new one:
  python taste\tools\author_run.py --resume CASE-20261102-1850 --kit --go --export-desk --publish
It starts at S2A. S1 is not paid for again.
