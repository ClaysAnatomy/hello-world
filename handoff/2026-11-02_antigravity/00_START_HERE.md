# Start here (for Aetherius)

This pack hands the MVP build to Google Antigravity, split across four agents. It is story-free. You do six things before any agent starts, then you paste one brief per agent and wait for reports. Nothing here spends authoring credits: no agent writes a case, makes an image or calls a model API.

## What is in the pack

| File | What it is | Who reads it |
|---|---|---|
| `00_START_HERE.md` | This sheet | You |
| `MVP_BUILD_PLAN.md` | The build plan, revision 3. The single source of truth for every agent | All agents |
| `01_ORCHESTRATION.md` | Who does what, in which order, on which branch, and how they hand over | All agents |
| `A1_WARDEN.md` | Brief for agent 1: verify, back up, secure, merge, hand over (Phases A and D) | Agent 1 |
| `A2_ENGINE_WRIGHT.md` | Brief for agent 2: bridge round two and the compound-query rule (Phase B) | Agent 2 |
| `A3_KIT_INTEGRATOR.md` | Brief for agent 3: import, verify and wire the authoring kit (Phase C) | Agent 3 |
| `A4_AUDITOR.md` | Brief for agent 4: read-only review at each gate, on a different model family | Agent 4 |

## Before any agent starts (about 20 minutes)

1. **Seal check: get spoiler folders out of the project folder.** Antigravity agents can search everything inside a workspace folder, and nothing confirms that they respect `.gitignore`. So no sealed folder may sit inside `D:\Project Recess\Project Mystery Machine\`. If `content\_SPOILERS_DO_NOT_OPEN` or any other SEALED or SPOILERS folder is still inside it, move it, as a sealed unit and without opening it, to `D:\_SEALED_DO_NOT_OPEN\`. Entry 004 set that as the target; Entry 022 left it open. If you are unsure, do this step anyway.
2. **Save the pack.** Put `MVP_BUILD_PLAN.md` in `docs\plans\` and the other files in `docs\handoffs\2026-11-02_antigravity\` inside the project.
3. **Fill section 0 of the plan.** BACKUP_PATH must be a folder on a physical drive that is neither D: nor H: (H: showed a Warning health flag in Entry 024). The other values are filled in already.
4. **Decide on the GitHub repository.** It is public. Nothing in it is story or secret, but you may prefer to make it private (GitHub: repository Settings, General, Danger Zone, Change visibility). The plan works either way.
5. **Antigravity settings, for every agent:**
   - Terminal execution: **Off, with an allow list** (safest), or Auto with the deny list in `01_ORCHESTRATION.md` section 5.
   - Browser use: off, if your version has the setting. The plan allows no network except one `git clone`.
   - Workspace: the folder each brief names. Agents 2 and 3 work in separate git worktrees, which contain only tracked files. Agent 4 works read-only.
6. **Models.** Builders (agents 1 to 3): the strongest coding model you have in Antigravity. Auditor (agent 4): a model from a **different family** from the builders. If the builders run on Gemini, run the auditor on Claude, or the other way round. This mirrors the research's cross-family rule.

## Then

1. Start **agent 1 (Warden)** alone and paste `A1_WARDEN.md`. Wait for its Phase A report and the `gate-A` tag.
2. Start **agent 2 (Engine Wright)** and **agent 3 (Kit Integrator)** together and paste their briefs. They work in parallel in separate worktrees.
3. When either reports a gate, start **agent 4 (Auditor)** with `A4_AUDITOR.md` and the gate name. Use a fresh conversation for each review.
4. Agent 1 merges, runs the final checks and writes the one summary you read. It ends with `SAFE TO MERGE` or `HOLD`.

## What you will see

Only IDs, counts, PASS/FAIL, file paths and command output. If an agent ever shows you story text, stop it: that is a seal breach. It should be impossible here, because every fixture is nonsense.

## What stays yours

Nothing in this pack pushes to GitHub, runs a live agent, spends credits, applies the look, or touches the vault. The tiny live probe, the first real case (`--go`) and the blind audit of that case all come after, and each needs your word. `MVP_BUILD_PLAN.md` section 6 lists them.
