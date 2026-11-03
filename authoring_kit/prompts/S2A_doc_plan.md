{{HEADER}}

# STAGE {{STAGE_ID}}: CUTTING THE STORY INTO PAPER

The story exists in `bible.json`. Now decide which documents this world would naturally have produced, and cut the story into them. The puzzle is the shape of that archive. Write no player-facing prose: every prose field gets a placeholder that later stages fill one document at a time. This stage writes only the plan.

## INPUT
{{INPUT_FILES}}

## OUTPUT
{{OUTPUT_FILES}}

## Turns
{{TURN_BUDGET}}

## Method

### 1. List the paper trail before you choose anything
Walk through the bible's timeline and ask, at each step, what paper the institution's ordinary work would have produced: rosters, logs, slips, notes, minutes, invoices, transcripts. Add the paper the cover story generated afterwards. Add the paper of the institution's everyday life that has nothing to do with the case. Most of the real archive was written by people who did not know what they were recording.

### 2. Choose and shape the documents
Pick the documents the player will see from that trail. For each one, the plan records:
- `form_id` from the catalogue below; `author` (a person ID or a department ID); `intended_reader`; `in_world_reason` (why it was written, in the author's terms). Ask: would this paper exist if nobody ever investigated? If not, it is a clue in costume. Re-cut it.
- `facts`: the bible fact IDs this document carries. `mentions`: the people it names.
- `tier`: 0 for documents available at the start, rising with each gate or delay the engine applies. The engine decides reachability; the tier is your declared order.
- `search_free`: true if a player can reach this document by reading and following references, with keyword search switched off.
- `role`: `solution`, `support`, `herring_induce`, `herring_refute`, `mask`, `reframe` or `world`.
- `technique_ids`: optional, from the technique list below.

### 3. Build the routes
For every solution-critical fact, list routes in `routes`: each route is a set of documents that together establish the fact. At least {{MIN_ROUTES}} routes per fact; two of them share no document; at least one route uses only search-free documents. No single document may carry every supporting fact of a correct option.

### 4. Place the turn and the false lead
- The masking document sits at a lower tier than the reframing document. No document lists the aha conclusion fact: the player assembles it.
- The herring's inducing document is at tier {{HERRING_MAX_TIER}} or lower. The documents carrying its refuting facts sit at a higher tier. A document establishes the secondary secret.
- Follow each pattern brief's pre-signalling list.

### 5. Give people a life on paper
Each suspect appears in at least {{MIN_DOCS_PER_SUSPECT}} documents written by at least {{MIN_AUTHORS_PER_SUSPECT}} different authors, and at least once in a document with no solution-critical fact: a rota swap, a complaint about the heating, a birthday collection. World documents make up between {{WORLD_MIN}} and {{WORLD_MAX}} of the archive, and each involves a named person.

Every world document also declares a `purpose`, because non-clue paper is never padding. Choose one `kind`:
- `teaches_rule`: it shows the player how this world works, by naming one of the setting's internal terms in `term`;
- `character_dynamic`: it shows how two or more named people stand with each other (list them in `people`; each appears in the document or wrote it);
- `setting_mechanic`: it establishes a routine, a constraint or a piece of equipment the case relies on.
Write one line in `note` saying how.

### 6. Departments and voices
The kit assigned these voice profiles to department slots, in order:
{{VOICE_SLOTS}}
Map the case's departments onto the slots in that order and record it in `departments`. Department-processed documents keep raw findings and assessment in separate fields. The finding is plain; the assessment carries the department's bias.

### 7. Decide which papers reach the player as objects
Some documents are better met as physical artifacts: a photograph pinned to a board, a scanned badge, a page torn from the station newsletter, a stamped report form, a handwritten note. Dress a document as one by adding `media` to its plan entry, with a `kind` from the media forms below. The kit then calculates every number, date, imprint and surface the artifact shows (report numbers in filing order, badge numbers in hiring order, frame counts in shooting order, the right weekday on a dateline, how the paper has aged in this climate), so nothing on any artifact can contradict anything else. You decide what the artifact is; you never write those values.

For a media document:
- `kind`; `depicts`: the people (cast IDs) or places (location IDs) an image shows; `camera`: a camera ID for photographs and video; `publication`: a publication ID for newspaper pages; `taken_at` (HH:MM) where the artifact prints a time; optional `handling` (0 to 5: how many hands it passed through) and `storage` (filed, boxed, pinned, pocket or framed).
- `regions`: map each of the form's text regions (prose, handwriting or depiction) to one of this document's placeholders. A depiction region gets its own placeholder with `kind: depiction`: in S3 the writer describes plainly what the image shows, and that text drives the image and its alt text. Depiction placeholders never appear in `case.json`.
- Optionally `anomaly`: one shown value deliberately differs from what the kit would calculate (a report number out of sequence, a backdated stamp), because the difference is evidence. Give `value_key`, the `value` shown, and the `fact` it carries. Never use an anomaly for anything else.

Then add `media_environment` to the plan: `climate` and `hemisphere`; `cameras` (each with an `id` such as CAM-1, a `kind` and an optional `owner`); `publications` (each with an `id` such as PUB-1, a short `name`, a `founded` date and `cadence_days`); and optionally `institution_code` (two to four capitals) or `archive_date`.

Use media where the object itself matters to the experience, not everywhere. Everyone an image shows needs a fixed `appearance` in the bible.

Media forms:
{{MEDIA_FORMS_TABLE}}

Media limits: {{MEDIA_LIMITS}}

### 8. List every placeholder
Every player-facing prose field of every document, and every desk field, will hold a placeholder token in the format `{{PLACEHOLDER_FORMAT}}`. Here `owner` is the document ID for document prose (filled in stage S3), or `{{S4_OWNER}}` for desk fields that belong to no single document, such as option wording, question stems, mail and subjects (filled in stage S4). `n` counts from 1 within each owner. Use the authoring contract {{AUTHORING_README}} to know which prose fields each kind of record has.

List every placeholder in `placeholders`, with:
- `slot`: which field it is, in the contract's terms; `kind`: one of the enum values.
- `facts`: the bible fact IDs that text may assert (a subset of its document's facts). Titles and subjects usually assert none.
- `required_strings`: critical-string IDs that must appear in it verbatim. Every critical string is required somewhere.
- `max_words`, and for option or stem placeholders the `question` and `option` IDs.

You do not write the engine files: the next stage builds `case.json` and `skin.json` from this plan exactly.

## Document forms
{{FORMS_TABLE}}

## Techniques
{{TECHNIQUES_TABLE}}

## Limits
{{LIMITS_TEXT}}

## Engine terms resolved for this run
{{CAPABILITY_TERMS}}

## The kit will check
{{CHECK_LIST}}
Write `clue_plan.json` in one write. Then reply `DONE`.
