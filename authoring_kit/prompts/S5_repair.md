{{HEADER}}

# STAGE {{STAGE_ID}}: REPAIR OF {{TARGET_UNIT}}, ROUND {{ROUND}} OF {{MAX_ROUNDS}}

Your earlier output for {{TARGET_UNIT}} did not pass. The failures are listed below as check IDs, the location in your files where known, and what each check requires. Fix exactly these. Change nothing that is not needed to fix them, so everything that already passed keeps passing.

## INPUT
{{INPUT_FILES}}

The original stage brief is `{{TARGET_BRIEF_FILE}}`. Your previous outputs are in `previous/`.

## OUTPUT
{{OUTPUT_FILES}}

## Failures
{{FAILURES_TABLE}}

## Rules for a repair
1. Start from your previous outputs; copy them and change only what the failures require.
2. Keep every name, ID, time and code exactly as it was unless a failure is about that value.
3. If a failure cannot be fixed without changing the story's truth, keep the truth and change the paper.
4. If the same check fails again in the next round the run stops for a human, so fix the cause, not the symptom.

Write the outputs. Then reply `DONE`.
