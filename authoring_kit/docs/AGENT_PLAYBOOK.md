# Agent playbook (Mode B)

For any agent with local file access working interactively. Follow it exactly. You are writing a case for a player who must stay blind, so the seal comes first.

## The seal

1. Never paste, quote, summarise or describe case content in the conversation. Your replies are IDs, counts and PASS/FAIL, as the kit prints them.
2. For each stage, read only the files the stage prompt lists under INPUT, inside that stage's folder. Write only the files listed under OUTPUT, in the same folder.
3. Never open the vault or any other case folder. Never open `checkpoints\` yourself; the kit puts what you need into the stage folder.
4. Do not edit kit files, engine files or anything outside the stage folder.

## The loop

1. Run `python authoring_kit\python\kit_run.py next --ws <case folder>`. It prints `NEXT <unit> READY` and `PROMPT stages/<unit>/prompt.md`.
2. Open `<case folder>\stages\<unit>\prompt.md` and do exactly what it says. Paths in the prompt are relative to that folder.
3. Run `python authoring_kit\python\kit_run.py check --ws <case folder>`.
4. If the check passes, go back to step 1.
5. If it fails, run `python authoring_kit\python\kit_run.py repair --ws <case folder>` and follow the new prompt, then `check` again. Fix only what the failure table lists.
6. When `next` prints `All stages passed. Run finish.`, run `python authoring_kit\python\kit_run.py finish --ws <case folder>`.
7. If the kit prints `ABORT` or `BUDGET STOP`, stop and report the printed lines to the human. Do not try to work around them.

## Fresh context per stage

Treat each stage as if you had never seen the earlier ones. In particular, while writing an S3 document, do not use anything you remember from S1 or S2: the S3 prompt holds everything that document may know. If your tool can start a fresh session per stage, do so. Mode A does this by construction.

## Done means

`FINISH PASS`. Report the kit's printed lines, nothing else.
