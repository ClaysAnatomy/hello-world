# Agent playbook (Mode B)

For any agent with local file access working interactively. Follow it exactly. You are writing a case for a player who must stay blind, so the seal comes first.

## The seal

1. Never paste, quote, summarise or describe case content in the conversation. Your replies are IDs, counts and PASS/FAIL, as the kit prints them.
2. For each stage, read only the files the stage prompt lists under INPUT, inside that stage's folder. Write only the files listed under OUTPUT, in the same folder.
3. Never open the vault or any other case folder, including the case folder named in `--ws`. Never open `checkpoints\` yourself; the kit puts what you need into the stage folder.
4. Do not edit kit files, engine files or anything outside the stage folder.

## The loop

1. Run `python authoring_kit\python\kit_run.py next --ws <case folder>`. It prints `NEXT <unit> READY` and `PROMPT <path>`. The path is a stage folder outside the case folder.
2. Open that `prompt.md` and do exactly what it says. Paths in the prompt are relative to its folder. Work only in that folder; the kit deletes it once the unit is accepted.
3. Run `python authoring_kit\python\kit_run.py check --ws <case folder>`.
4. If the check passes, go back to step 1.
5. If it fails, run `python authoring_kit\python\kit_run.py repair --ws <case folder>` and follow the new prompt, then `check` again. Fix only what the failure table lists.
6. When `next` prints `All stages passed. Run finish.`, run `python authoring_kit\python\kit_run.py finish --ws <case folder>`.
7. If the kit prints `ABORT` or `BUDGET STOP`, stop and report the printed lines to the human. Do not try to work around them.
8. If the kit prints `AGENT <unit> paused`, a usage limit was reached. Stop. Running `next` later restarts the same unit.

## The blind audit (S7)

The audit must be done by an agent of a **different model family** from the one that wrote the case, and that agent must not have seen the authoring stages. Run `kit_run.py audit --ws <case folder> --bundle <player bundle>`, then in a fresh session open each printed prompt (SHORTCUT first, then SOLVE), write `answers.json` as asked, and run `kit_run.py audit-score --ws <case folder>`. Reply only with the printed lines.

## Fresh context per stage

Treat each stage as if you had never seen the earlier ones. In particular, while writing an S3 document, do not use anything you remember from S1 or S2: the S3 prompt holds everything that document may know. If your tool can start a fresh session per stage, do so. Mode A does this by construction.

## Done means

`FINISH PASS`. Report the kit's printed lines, nothing else.
