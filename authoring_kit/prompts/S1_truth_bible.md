{{HEADER}}

# STAGE {{STAGE_ID}}: THE STORY AND ITS TRUTH

You are building the front of the box: a story worth reading with the puzzle taken away. Write no player-facing prose in this stage. You are writing the sealed bible that every later stage depends on.

## INPUT
{{INPUT_FILES}}

## OUTPUT
{{OUTPUT_FILES}}

## What you were given
{{BRIEF_STATUS}}

Treat the brief, if any, as anchors. Keep every concrete thing it asks for. Where it is vague, choose the specific version. Where it is silent, use the seeds below. Record in `premise.anchors_honoured` each anchor you kept, in a few words. A brief can be one word or many pages; the method is the same.

## Seeds chosen by the kit (use them; do not swap them)
{{SEEDS_TABLE}}

## Aha pattern briefs for this case
{{PATTERN_BRIEFS}}

## Work in this order. Do not skip ahead.

### 1. The world before anything went wrong
Build one specific institution in one specific place and time. Fill `premise.setting`:
- `before_problem`: the trouble this place was already having last month, unrelated to any crime: a budget cut, a merger, a retirement, a backlog, a broken machine nobody will pay to fix. The case should grow out of this.
- `texture`: at least {{MIN_TEXTURE}} concrete things a person working there would see, hear, handle or smell. Objects and routines, not adjectives.
- `internal_terms`: at least {{MIN_TERMS}} words or abbreviations staff use without explaining them, each with its meaning.
- `rhythms`: at least {{MIN_RHYTHMS}} recurring times the place runs by (shift change, delivery day, quarter end). Documents will be stamped by these.

### 2. People before suspects
The cast names are fixed by the seeds. Assign each seeded name to one person. For every person, fill the sheet:
{{PERSON_SHEET}}

Then put each person through these tests and revise until they pass:
{{PERSON_TESTS}}

Give each person at least {{MIN_RELATIONSHIPS}} relationships to other named people, each with history and a current temperature. Between {{MIN_SUSPECTS}} and {{MAX_SUSPECTS}} people are suspects. The person at the centre of the case (`role: subject`) had a want and an obligation too.

### 3. What actually happened
Write `truth.what_happened` as the plain, complete account an omniscient clerk would file: who did what, in what order, where, and for which human reason. Then write `truth.timeline` as dated or timed steps. Use the critical strings from the seeds exactly where the story needs a decisive time or code, and give each a `meaning` in `critical_strings`.

The culprit acts for a reason a fair-minded colleague could explain without calling them evil, mad or greedy. Write it in `truth.why_it_matters`: what the act protected or obtained for them. Root it in the seeded stakes.

Write `cover`: the official story the institution, or the culprit, put on paper afterwards, and who keeps it up. Most of the archive will have been written by people who believe the cover.

### 4. The shape of the revelation
- `premise.human_question`: what the case is really about, as a question. Start from the seeded question; sharpen it for these people.
- `premise.central_irony`: start from the seeded irony; make it specific.
- `premise.hook`: one sentence that makes a stranger ask what happened next. It must be compelling without the solution. If it needs the answer to be interesting, the story is not ready: go back to step 2.
- `premise.ending_note`: the image or fact the player keeps once they know the truth. The truth should change what the human question means.

### 5. The turn and the false lead
- For each seeded pattern, fill one `aha` entry. `mask_fact` is the ordinary-looking fact planted early, `reframe_fact` is the later fact that changes its meaning, and `leads_to_fact` is the conclusion the player must reach alone. Three different facts. Follow the pattern brief's pre-signalling list.
- `red_herring`: use the seeded type. It belongs to a suspect who is not the culprit and rests on a true secondary secret (a fact of kind `secondary`). It points to a wrong option. `refuted_by_facts` lists the facts that dismantle it cleanly. The false lead must deserve real suspicion; a reader should feel foolish for dropping it too early, not for believing it.

### 5a. Familiar things, made new
Well-worn tropes are welcome when they are chosen. If the brief asks for one, or the story reaches for one, embrace it on purpose: keep it recognisable enough to raise the genre's expectation, then renew it with a lens so the player sees it again. The mystery form suits this well: a trope can be the default reading that your aha pattern masks and later reframes.

For each trope you use on purpose, add an entry to `premise.tropes_embraced` with the trope in a few words, a `lens_id` from the table below, and `how` the lens renews it here. At most {{MAX_TROPES}}. Start with the lens the seeds suggest, unless another clearly serves the story better.

The trope lives in the structure. Its stock phrasing never appears in any document.

{{TROPE_LENSES}}

### 6. The facts
Break the truth into atomic facts, one checkable statement each. Kinds: `base` (observed), `derived` (follows from other facts; list them in `from`), `secondary` (the herring's true secret), `herring` (what the false lead seems to show), `world` (texture that asserts nothing about the case). Mark `solution_critical: true` on every fact the correct answers depend on. The method and motive facts named in `truth` are solution-critical.

### 7. The questions and options
Write the determination questions the engine expects (read the authoring contract for how many and of which kinds). Each option is a real possibility a careful reader could hold for a while: a real person, a real method, a real reason drawn from this world. Exactly one option per question is `correct`. Every option lists at least two supporting facts in `support`. Options are gists here; their wording is written later by a stage that will not see which is correct.

## Limits
{{LIMITS_TEXT}}

## Engine terms resolved for this run
{{CAPABILITY_TERMS}}
Use the authoring contract file {{AUTHORING_README}} to understand what the engine can express. Shape the truth so that it can be expressed.

## The kit will check
{{CHECK_LIST}}

Write `bible.json` matching `bible.schema.json`. Then reply `DONE`.
