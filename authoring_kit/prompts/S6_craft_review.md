{{HEADER}}

# STAGE {{STAGE_ID}}: CRAFT REVIEW (SCORES ONLY)

Read the bible, the plan and the finished case as an editor who cares about the reader. Score each item below from 0 to 3. You write no text at all: only scores and IDs.

## INPUT
{{INPUT_FILES}}

## OUTPUT
{{OUTPUT_FILES}}

## Scale
0 absent or broken, 1 present but weak, 2 solid, 3 exemplary.

## Items to score
{{RUBRIC_TABLE}}

## How to judge
- Hook: read the tier-0 documents only. Would a stranger want to open the next one, regardless of the puzzle?
- Voices: cover each document's header and author line. Can you still tell who wrote it?
- The turn: read the masking document as if for the first time. Does it read as ordinary? After the reframing document, does it read differently with nothing new added?
- Diegesis: for each document ask whether it would exist if nobody ever investigated.
- Honesty: do any titles, subjects or findings conclude rather than describe?

## Flags
Add to `flags` the ID of any failure mode you see clearly, from:
{{FM_TABLE}}

Write `review.json` matching `review.schema.json`. Then reply `DONE`.
