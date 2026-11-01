{{HEADER}}

# STAGE {{STAGE_ID}}: DESK FIELDS

Write the words the Desk shows around the documents: question stems, option wording, mail, subjects. You are not told which options are correct. Write every option as if it might be.

## INPUT
{{INPUT_FILES}}

## OUTPUT
{{OUTPUT_FILES}}

## Questions and their options (gists only, in no meaningful order)
{{QUESTIONS_TABLE}}

## Facts available to the fields below
{{FACTS_TABLE}}

## Real people and places in this case
{{ENTITY_LIST}}

## Names, spelled exactly
{{CAST_NAMES}}

## The world
{{WORLD_BRIEF}}

## Fields to fill
{{SLOTS_TABLE}}

## How to write them
1. Options within a question share one grammatical shape and one level of specificity. Their lengths stay within {{OPTION_TOLERANCE}} of each other. No option is more detailed, more hedged or more vivid than its neighbours.
2. Every option names at least one real person or place from the list above. A distractor is a possibility a careful reader could hold, never a joke.
3. Stems ask plainly. They never hint at how many steps lie behind them or which records matter.
4. Mail and subjects follow the institution's habits: a reference, a date, a routine subject. They assert only the facts assigned to them and never conclude.
5. Nothing tells the player they are close, clever or wrong.

## Claims
For every field, list in `claims` the fact IDs it asserts.

## The kit will check
{{CHECK_LIST}}

Write `fill.json` matching `fill.schema.json`, with `owner` set to `{{OWNER}}`. Then reply `DONE`.
