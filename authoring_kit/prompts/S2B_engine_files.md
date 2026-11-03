{{HEADER}}

# STAGE {{STAGE_ID}}: THE ENGINE FILES, FROM THE PLAN

The document plan is accepted. Turn it into the engine's own files, exactly. This stage is structure only: you write no prose, choose nothing new and change nothing in the plan.

## INPUT
{{INPUT_FILES}}

## OUTPUT
{{OUTPUT_FILES}}

## Turns
{{TURN_BUDGET}}

## Method
1. Write `case.json` and `skin.json` exactly as the authoring contract {{AUTHORING_README}} requires. Use the fixture files as the format example; they are nonsense and teach shape only.
2. Create one record per document in the plan, with the plan's document ID as its clue ID, its date, tier, department and relations to the facts it carries, in the engine's terms below.
3. Put every placeholder token from the plan's `placeholders` into its slot: the whole string is the token, and each token appears exactly once. Tokens of kind `depiction` never appear in the engine files: they belong to the media layer.
4. Reuse the bible's IDs for people, locations, solution-critical facts, questions and options unchanged.
5. Write dates, times, tiers and other non-prose fields directly, exactly as the plan and the bible give them.
6. The skin carries the departments in the plan, in order, with neutral labels.

Write each file in a single write, whole. Never append. Then reply `DONE`.

## Engine terms resolved for this run
{{CAPABILITY_TERMS}}

## The kit will check
{{CHECK_LIST}}
It then runs the engine's own checks on `case.json`.
