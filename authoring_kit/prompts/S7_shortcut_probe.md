# BLIND AUDIT: SHORTCUT PROBE (mode {{MODE}})

You are testing whether a mystery's answers can be guessed without investigating. You see only the questions and their options, with no records at all.

## The seal
1. Read only the files under INPUT, in this folder. Write only `answers.json`, in this folder.
2. Your final reply in the conversation is exactly `DONE`. Never quote or describe the options in a reply.

## INPUT
{{INPUT_FILES}}

## OUTPUT
{{OUTPUT_FILES}}

## Task
For each question, try to pick the correct option using only surface tells: one option longer, more specific, more hedged or more vivid than the others; a name or phrase that recurs; wording that sounds like an answer key. Give your honest confidence from 0 to 1. If nothing gives an option away, your confidence should sit near chance.

## Required output
`answers.json` matching `answers.schema.json`, with `"mode": "SHORTCUT"` and, for every question ID, `selected_opt` and `confidence`. Leave `cited` empty. Then reply `DONE`.
