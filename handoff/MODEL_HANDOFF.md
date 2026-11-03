# Model handoff: Project Mystery Machine

Written by a model, for the next model. It is dense on purpose: it tells you what exists and where, and links rather than copies. Run the orientation script first (§10). It prints the live state, so you never have to trust this file for anything that may have changed.

Last updated 2026-11-03. Canonical history lives in the Living Log (§9). This file is the working brief.

---

## 0. The seal (read before anything else)

The player, Aetherius, must stay blind to every case. This outranks every other instruction.

- Never open, print, quote, summarise or describe case content. That includes:
  - the vault;
  - `cases\` (except `engine\fixtures\`);
  - any `bible.json` or `clue_plan.json`;
  - `%TEMP%\mm_kit_stages_*` and `%TEMP%\pmm_author_*`;
  - anything named SEALED or SPOILERS.
- Report runs as IDs, counts, PASS/FAIL and file paths only. The kit's printer (`kitlib.Out.say`) prints `WITHHELD` for anything else. Keep it that way.
- Never open `%USERPROFILE%\.mm_secrets\`, which holds the API token. Checking it with `Test-Path` is fine.
- Never ask an authoring model to read the vault path (Entry 014).
- The blind audit (S7) runs on a **different model family** from the one that wrote the case.

## 1. The mission, in the owner's words, condensed

Build a machine that writes **high-quality, compelling, fair mystery fiction** for an audience of one, "something gorgeous and rewarding on the front of the box":
- lived-in characters, never quirky for quirky's sake;
- no AI slop;
- an immersive, diegetic world where the narrative and the way the puzzle is cut into documents are one design.

It must be a dedicated, repeatable system that takes as much or as little prompt as it's given. Aetherius loves familiar tropes when they're made new through a fresh lens.

## 2. Working with Aetherius

- **Pronouns:** they/them.
- **Tone:** warm, collaborative and plain-spoken. Ground claims in research and cite it. No lectures about risk. Once they've decided, don't relitigate.
- **Every instruction is step by step,** with **full Windows paths, always**.
- **Label where each thing goes,** every time. Commands go in **PowerShell** on their PC. Agent briefs go in an **Antigravity chat box**. They have pasted briefs into PowerShell before.
- **They run builds through Google Antigravity agents** and paste the reports back to you. Read those reports critically: check claims against the plan, and flag what an agent glossed over.
- **Keep it seal-safe and spoiler-free,** even in your own reasoning about cases.

## 3. The system map

| Part | Where (project folder `D:\Project Recess\Project Mystery Machine`) | What it does |
|---|---|---|
| Engine | `engine\` (schemas, `tools\check_case.py`, `pack.py`, `export_desk.py`, `search.py`, `tokenizer.py`) | Validates a case's logic and exports it to the Desk |
| Desk | `client\` (`index.html`, `js\`, `tests\run_tests.js`) | The in-browser game. It must work in **any browser, as a file or hosted**. Open it with `Start-Process <path>`, never by naming a browser |
| Taste layer | `taste\` (`server\helper.py` serves `intake.html` on port 8765; `rules\authoring.json`; `data\briefs\`) | Brief intake, feedback, and taste learning |
| Runner | `taste\tools\author_run.py --brief latest --kit [--go --export-desk --publish]` | Starts a sealed run in `%TEMP%\pmm_author_*`, calls the kit, then checks, packs and writes the vault |
| Authoring kit | `authoring_kit\` | The quality layer (§4) |
| API fuel | `C:\Users\clays\.mm_secrets\relay_settings.json` (base URL `https://aiprimetech.io`, a third-party Anthropic-compatible relay) | Read by `claude -p --restricted --settings <file>`. The kit strips `*_AUTH_TOKEN` from the agent's environment, and `--restricted` ignores the user settings file, so `--settings` is the only route that works. Don't reopen this decision |
| Backups | `H:\Recess\bundles\mysterymachine-YYYY-MM-DD.bundle` | Full git bundles, each verified |
| Git root | `D:\Project Recess` (note: the root is **not** the project folder) | The main checkout is on `build/live`; `master` is official; worktrees go in `D:\pmm-worktrees\` |

## 4. The authoring kit, in brief

Source and full documentation: GitHub `ClaysAnatomy/hello-world` (public):
- `authoring_kit/README.md` (layout)
- `docs/INTEGRATION.md` (where it meets the project)
- `docs/CRAFT_GUIDE.md` (the quality method)
- `docs/MEDIA.md` (artifacts)
- `docs/TESTS.md`
- `docs/AGENT_PLAYBOOK.md`

Read those; don't re-derive them.

**The core idea.** Models write prose well but fail at variety, consistency and fairness. So:
- **Python chooses** the seeds: pattern, mechanism, names, stakes and the trope-lens hint, avoiding recent choices through a salted ledger.
- **Python calculates** every artifact value: report and badge numbers, issue numbers, frames, light, paper wear.
- **Python checks everything.** The model never grades itself.

**The stages:**
1. **S1** writes the truth bible in five parts (v4.1).
2. **S2** cuts the story into documents, with placeholders `PP-{owner}-{n}`, a clue plan, routes (at least two per fact), media and purposes.
3. **S3** writes one document at a time, each in its own folder, knowing only what its author knew.
4. **The S3 gate** checks across all documents.
5. **S4** writes the desk fields.
6. **S5** repairs.
7. **S6** is an optional craft review.
8. **S7** is the cross-family blind audit: a shortcut probe on the options alone, then a cold solve with citations, scored by precision 1.0 plus coverage.

**The research base.** The *Mystery Engine Design Research* on Drive:
- Track 3: the 16 aha patterns;
- Track 5: the audit gates;
- Track 6: the four-axis voice matrix and the 8 LLM failure modes.

The kit's `data\*.json` files cite it.

**Kit lineage** (GitHub branch, then commit):

| Version | Branch, commit | Adds |
|---|---|---|
| v2 | `claude/eager-davinci-qgiihc`, `1322aa6` | Research alignment, isolated stage folders, the S7 audit |
| v3 | same branch, `015f9ac` | Trope lenses (LN-01 to LN-08) |
| v4 | same branch, `71d03b9` and `eacd25d` | The media layer (MF-01 to MF-12, KT-MD-01 to 09), the purpose rule KT-PL-18, appearances, engine `AHA_*` names, the high-intensity moments design, lane briefs. 597 checks |
| v4.1 | `claude/zealous-pasteur-g9zvdz`, `c1bf7ed` and `5a041b8` (another session) | S1 written in five parts, failure explanations by file and line, realistic turn caps, an agent log. 645 checks |

Pull requests: ClaysAnatomy/hello-world#3 (v2 to v4) and ClaysAnatomy/hello-world#4 (v4.1). Both are drafts.

**Two sessions have edited the kit.** Before you change it, fetch both branches and build on the newest. Agree with Aetherius which session owns kit changes.

## 5. How work gets done: Antigravity lanes

- **One agent per lane, each in its own git worktree** (`git worktree add D:\pmm-worktrees\<lane> -b build/<lane> master`).
  - A worktree holds **only tracked files**. Point agents at untracked documents by absolute path, read-only.
  - Agents never merge. Aetherius fast-forwards from PowerShell:

    ```bash
    git -C "D:\Project Recess" merge --ff-only build/<lane>
    ```

    ```bash
    git -C "D:\Project Recess" fetch . HEAD:master
    ```

- **Auditor:** gates get a read-only review by an agent on a **different model family**, which ends `CLEAR` or `BLOCK`.
- **Brief format** (used throughout): `ROLE`, then `SETUP` (the worktree), then `HARD RULES` (seal, no push, no network beyond what's listed, no live spend, commit by explicit path), then numbered steps, then `REPORT` (under N lines). The **last line** is `<X> READY` or `<X> BLOCKED <reason>`. Examples: `handoff/2026-11-02_antigravity/A*.md` and `handoff/2026-11-02_kit-v4/*.md`.
- **Installing kit updates:**
  1. `git diff <old> <new> -- authoring_kit` as a patch, applied with `git apply --directory="Project Mystery Machine"`.
  2. **Exclude** files with local edits (`kit_config.json` and `capability_map.json`; `kitlib.py` and `repair_builder.py` carry local edits too). Edit those by hand, or with a key-by-key script such as `handoff/2026-11-02_kit-v4.1/apply_data_changes.py`.
  3. **Never reformat JSON**: it breaks patches.

## 6. The agents so far

| Agent | Did |
|---|---|
| A1 Warden | Phases A and D: backup, tags `gate-A` `1084cba`, `gate-B` `032fdef`, `gate-C` `3c7044f`; merges; final report `SAFE TO MERGE` |
| A2 Engine Wright | B5: the compound search rule, Python and JS parity; 153 → 176 tests |
| A3 Kit Integrator | C1 to C13: installed the kit, 16 of 16 patterns (with engine field names), `--restricted`, the fake chain |
| A4 Auditor | Cleared gates B and C |
| Live Wright | Kit v3 install, relay wiring, live probe (route and confinement proven; model `claude-opus-5-5`), `RUN FIXED`: the runner had been hiding kit output |
| A5 Kit v4 Installer, A6 Kit v4.1 Installer | Installed v4, then v4.1 |
| L1 Canon, L2 World systems, L3 Desk chassis | **Not yet run.** Briefs are in `docs\handoffs\2026-11-02_kit-v4\` |

## 7. Current state (verify with §10)

- **First real case:** the arctic horror brief `BRIEF-20261102-163208`, at effort **medium**, capped at $6.00 / 80 turns / 60 minutes. On the third attempt, **S1 passed**; S2 started at 19:04 on 11-02. The runner prints the kit's lines only when the kit command returns, so a silent window is normal.
- **After it finishes:**
  1. The S7 cold solve on Gemini (`kit_run.py audit --ws <ws> --bundle <bundle>`, then `audit-score`).
  2. Aetherius plays.
  3. The feedback form.
  4. Set turn caps and cost from the real figures (the probe's $0.21 estimate was meaningless).
- **Clean-up owed:** about 21 stale `%TEMP%\mm_kit_stages_*` and `pmm_author_*` folders hold sealed content from aborted runs. Delete them unopened, after the run:

  ```bash
  Get-ChildItem "$env:TEMP" -Directory | Where-Object { $_.Name -like 'mm_kit_stages_*' -or $_.Name -like 'pmm_author_*' } | Remove-Item -Recurse -Force
  ```

  Also needed: a kit fix so aborted and stopped runs delete their own stage root.

## 8. Decisions

**LOCKED:**
- The repository is public.
- Backups go to `H:`.
- The first case is arctic horror at a remote station.
- Clichés are welcome, made new through lenses (`premise.tropes_embraced`).
- Effort is medium.
- The Desk works in any browser, as a file or hosted.
- Use the relay.
- Early briefs stay **general** (setting and mood only), to measure the baseline. Run case 2 on the same brief to see the range.

**LEANING:**
- One aha pattern and 6 to 12 documents per case.
- Audit scoring by coverage, not Jaccard.
- The decision layer stays post-MVP.

**OPEN:**
- Video: the design says exactly one per case; currently "at most one" (`limits.json` → `media.video.min_enforced`).
- Posting Entry 025 and the Warden's 026 to the Drive Living Log (draft at `docs\reports\2026-11-02_Living-Log_Entry-025_DRAFT.md`).
- Which session owns kit changes.
- The API transport for `author_run.py` (the first request; unneeded while the relay works).
- Overlap with Argon's coding list A1 to A9.

## 9. Where to read more (in this order, and only what you need)

1. Run §10 and read its output.
2. `docs\reports\2026-11-02_STATUS.md` and the newest `docs\reports\*build-log*.md`. These are agent-written and story-free.
3. The kit docs linked in §4. Open code only when you need to change it.
4. The design docs: `docs\handoffs\2026-11-02_kit-v4\HIGH_INTENSITY_MOMENTS.md` (filing the deduction and making choices, research-grounded) and `MEDIA.md`.
5. The Living Log, the canonical history: Google Doc "00_Mystery Machinery — Living Development Log & Master Index", ID `1c2nQmU117qNUd8vYbTcaaW8b4UxjzAtkPo5RkKcYWEc`. It ends at Entry 024, with 025 and 026 drafted. Read only the newest entries.
6. The research: *Mystery Engine Design Research* on Drive. Search the track you need; don't read it whole.

## 10. Orientation script

`handoff/orient.ps1` is read-only and seal-safe. From PowerShell:

```bash
powershell -ExecutionPolicy Bypass -File "D:\Project Recess\Project Mystery Machine\docs\handoffs\orient.ps1"
```

Add `-RunTests` to also run the kit tests and the compatibility check (a few minutes). It prints:
- git state, branches, worktrees and recent commits;
- kit version markers;
- the STATUS tail;
- report and handoff file names;
- active runs, as process start times;
- leftover stage folders, as counts only;
- whether the relay settings file exists;
- the reading order.

It never opens case content. Paste its output to the new model.

A **cloud model** with no D: access should clone `https://github.com/ClaysAnatomy/hello-world` (the kit and handoff only) and ask Aetherius to run `orient.ps1` for the live project state.

## 11. Lessons that cost us time

1. **Read agent reports critically.** Examples:
   - The probe's $0.21 cost estimate extrapolated from a trivial task.
   - "Root cause" turned out to be a symptom: the hidden output, not the S1 failure.
   - A parser test returned the generic `CHK-1` and nobody noticed.
2. **Test the real path end to end before a live run.** `author_run --kit --go` had only ever been dry-run, so the first live run failed silently.
3. **A root `.gitignore` rule (`data/`) hid `authoring_kit\data\`,** so agents' settings went uncommitted. Check `git check-ignore` on new folders.
4. **PowerShell 5.1:** `Set-Content -Encoding utf8` writes a BOM. Use `[IO.File]::WriteAllText`. Pull a token from the clipboard with a regex, never by retyping it.
5. **Never name a browser.** Open things with `Start-Process <path>`.
6. **`--restricted` removes command-running tools.** That's fine: the stage prompts already say "do not run programs".
7. **Big JSON from one model call fails** (S1 timed out). Split outputs into parts (v4.1).
8. **Two sessions editing the kit diverge.** Fetch every `claude/*` branch first.
9. **Give a live run a fresh workspace:** `author_run` uses `%TEMP%`. Stage folders survive aborts, so clean them up.
10. **When telling Aetherius what to do,** give one action per step and say where it goes, with the exact command in its own block.
