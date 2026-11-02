{{HEADER}}

# STAGE {{STAGE_ID}}: ONE DOCUMENT, {{OWNER}}

Write one document. You know only what its author knew and what this document must carry. You do not know the solution, and you do not need it.

## INPUT
{{INPUT_FILES}}

## OUTPUT
{{OUTPUT_FILES}}

## The document
{{FORM_BRIEF}}

- Written by: {{AUTHOR_BRIEF}}
- Written for: {{READER}}
- Why it exists: {{REASON}}
- Dated: {{DATE}}

## The object
{{MEDIA_BRIEF}}

## The world it was written in
{{WORLD_BRIEF}}

## The voice
{{VOICE_BRIEF}}

## The facts this document carries, and nothing more
{{FACTS_TABLE}}

## Exact strings that must appear, verbatim
{{REQUIRED_STRINGS}}

## Names, spelled exactly
{{CAST_NAMES}}

## The other papers in this archive
These exist alongside this document. The author may refer to one the way people do at work ("see the rota for 4 March", "as per Tuesday's slip") if it fits their business. Never cite reference numbers: the Desk assigns those later. Nothing here tells you what those papers say, and you must not invent their contents.
{{NEIGHBOURS}}

## Fields to fill
{{SLOTS_TABLE}}

## How to write it
1. Write as the author, for the reader, about the author's own business. The author does not know a mystery is being read. They are filling in a form, handing over a shift, complaining, asking for supplies, keeping a record.
2. Carry each assigned fact in the detail the author would naturally record: a time in a log, a count on a slip, a name in a margin. State only the raw observation; never state what it proves about anyone or anything. Never point at it, explain it, or set it apart.
3. You may add texture that asserts nothing about people, times, places or events in the case: the form's printed headings, the weather, a stain, the author's habitual sign-off. Texture makes the paper real. It must never smuggle in a fact.
4. Let the author's habit of attention decide what is detailed and what is skipped. What a person notices is how the reader meets them.
5. Titles and subjects are filed the way the institution files things: by form, number, date or routine subject. They describe; they never conclude.
6. Findings, if this document has them, are plain observation: measurements, counts, positions, times. All interpretation goes in the assessment field, in the voice above.
7. Stay inside each field's word limit. Shorter is usually stronger.

## Claims
For every field, list in `claims` the fact IDs that field asserts. Every fact assigned to a field is claimed by that field, and nothing else is.

## The kit will check
{{CHECK_LIST}}

Write `fill.json` matching `fill.schema.json`, with `owner` set to `{{OWNER}}`. Then reply `DONE`.
