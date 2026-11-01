# Orchestration: four agents, one build

Story-free. Read with `MVP_BUILD_PLAN.md` (revision 3), which holds the work itself. This file says who does each part, where, in what order, and how the agents hand over without stepping on each other.

## 1. The roster

| Agent | Name | Phases | Workspace folder | Branch | Model |
|---|---|---|---|---|---|
| 1 | Warden | A, merges, D | the project folder on D: | current, then `build/mvp` | strongest coding model available |
| 2 | Engine Wright | B | `D:\pmm-worktrees\b` | `build/mvp-b` | strongest coding model available |
| 3 | Kit Integrator | C | `D:\pmm-worktrees\c` | `build/mvp-c` | strongest coding model available |
| 4 | Auditor | reviews at gate-B, gate-C and final | read-only: whichever worktree or branch is under review | none (never commits) | a **different model family** from agents 1 to 3 |

Why this split: Phase B (engine and Desk search) and Phase C (authoring kit) touch disjoint files, so they can run in parallel. Each runs in its own git worktree, which also means the agent's workspace holds only tracked files: no ignored or sealed folder can be inside it. The Warden alone touches the main checkout, backups, tags and merges, so one agent owns anything irreversible. The Auditor is a different family from the builders because the builders wrote the code and the tests (the research's cross-family rule, applied to engineering).

## 2. The sequence

```
Warden:     A1 → A2 → A3 → A4 → A5 (gate-A, branches, worktrees) ─────────────► D1 merge B ──► D1 merge C ─► D2..D5
                                     │                                          ▲                ▲
Engine W.:                           └► B1 … B6 → GATE B (gate-B) ─► Auditor ───┘                │
Kit Int.:                            └► C1 … C11 ─(wait for B merged)─► merge build/mvp → C12 → C13 → GATE C (gate-C) ─► Auditor ─┘
```

1. The Warden runs Phase A alone. Nobody else starts until `gate-A` exists and the STATUS file says `A DONE`.
2. The Engine Wright and the Kit Integrator start together.
3. The Kit Integrator stops after C11 and waits for STATUS to say `B MERGED`. It then merges `build/mvp` into `build/mvp-c` (merge commit, no rebase), reruns the kit tests, and continues with C12, C13 and GATE C.
4. Each gate gets an Auditor review in a fresh conversation. The Warden merges a branch only after the Auditor's verdict for that gate is `CLEAR`.
5. The Warden runs Phase D and writes the one report Aetherius reads.

## 3. Who may edit what

| Area | Owner | Everyone else |
|---|---|---|
| the Python tokenizer and search modules under `engine\tools\` and the reachability computation in `engine\tools\lint.py` (compound rule only), `engine\fixtures\CASE-FIX-03\`, broken variants, `engine\tests\`, `client\js\search.js`, `client\js\tokenizer.js`, `client\tests\vectors\` (B5 only), image brief schema (B4) | Engine Wright | read-only |
| `incoming\`, `authoring_kit\`, `taste\tools\author_run.py` (`--kit` only), `.gitignore` (`incoming/` line only), the pointer appended to `engine\README_AUTHORING_FOR_OPUS.md` | Kit Integrator | read-only |
| Backups, tags, branches, worktrees, merges, `docs\CODEBASE_STATE.md`, `docs\reports\2026-11-02_STATUS.md`, the Living Log draft | Warden | read-only |
| Each agent's own `docs\reports\2026-11-02_build-log_<agent>.md` | that agent | read-only |
| Everything | | Auditor: read-only, always |

If an agent needs a file it does not own, it stops and writes `NEEDS <file> FROM <owner>` in its build log. The Warden decides, records the decision in STATUS, and the owner makes the change (plan section 5, item 10).

## 4. Coordination by files

The agents do not talk to each other. They read and write files:

- **STATUS** (`docs\reports\2026-11-02_STATUS.md`, Warden only). One line per event: `A DONE`, `B GATE`, `B CLEAR`, `B MERGED`, `C GATE`, `C CLEAR`, `C MERGED`, `STOP <agent> <reason>`. The Warden also records here which project folder each worktree uses.
- **Build logs** (one per agent). One line per decision, gate and stop, in the agent's own file.
- **Gate reports.** At each gate, the building agent writes `docs\reports\2026-11-02_gate-<X>.md`: the commands run, their exact pass counts, the files changed (`git diff --name-only gate-A..HEAD`), and anything ALREADY DONE. That is what the Auditor reviews.
- **Audit reports.** The Auditor writes `docs\reports\2026-11-02_audit-gate-<X>.md` into the worktree under review, untracked, and the Warden copies it into the main checkout. The verdict is the last line: `CLEAR` or `BLOCK <reason>`.

When a gate or review starts, Aetherius (or the Agent Manager) tells the next agent which file to read. No agent polls in a loop.

## 5. Antigravity settings

- **Terminal execution.** Safest: Off, with an allow list. Allow `git status`, `git log`, `git diff`, `git show`, `git rev-parse`, `git branch`, `git worktree`, `git tag`, `git add <explicit path>`, `git commit`, `git merge`, `git bundle`, `git clone` (agent 3, C1 only), `git checkout`, `python`, `node`, `py`. If you use Auto instead, deny at least: `git push`, `git reset`, `git rebase`, `git clean`, `git commit --amend`, `git add .`, `git add -A`, `rm`, `rmdir`, `del`, `Remove-Item`, `curl`, `wget`, `Invoke-WebRequest`, `Invoke-RestMethod`, `Start-Process`, `npm install`, `pip install` (except `pip install jsonschema` if it is missing).
- **Browser.** Off for every agent. The plan allows no network but one clone.
- **Review policy.** Ask for review before any command outside the allow list. An approval prompt for something the plan does not cover is a STOP (plan section 5, item 6), not something to click through.
- **Conversation records.** Antigravity keeps conversation records (Entry 016). Nothing in this build is story, but keep it that way: no agent pastes file contents from outside its lane into the conversation.

## 6. The Auditor's protocol

At each gate, a fresh Auditor conversation gets `A4_AUDITOR.md`, the gate name and the gate report path. It:

1. Runs the read-only checks for that gate in a clean place (a fresh temporary clone of the branch, or the worktree without editing).
2. Applies the review checklist in section 1 of `docs\handoffs\2026-11-01_uiux-conversation_context.md`.
3. Compares the gate report's claimed counts with its own run.
4. Ends with `CLEAR` or `BLOCK <reason>`. A BLOCK goes back to the building agent, who fixes only what the BLOCK names and re-reports the gate.

The Auditor never edits a tracked file, never commits, and never pushes.

## 7. Failure handling

- **STOP in one lane** pauses only that lane. The Warden records `STOP <agent> <reason>` in STATUS; the other lane continues unless the STOP touches shared state (backups, tags, merges, `.gitignore`).
- **A merge conflict** in a log or STATUS file: keep both sides. A conflict in logic: STOP (plan section 5, item 10).
- **A failed gate twice in a row** with the same rule or test: STOP for Aetherius.

## 8. Done means

STATUS ends with `C MERGED` and `D DONE`; the Warden's final report ends with `VERDICT SAFE TO MERGE` or `VERDICT HOLD <reason>`; every worktree is removed; and no push has happened.
