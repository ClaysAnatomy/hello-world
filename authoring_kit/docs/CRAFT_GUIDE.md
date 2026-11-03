# Craft guide: the front of the box

This kit exists for one reason: every sealed case should be a story worth reading even with the puzzle taken away, and then cut into the paper its world would really have produced. The checks, caps and stages protect that. They are not the point.

This guide is for people (and for a reviewing model) who want to understand *why* the prompts ask for what they ask. The operational version lives in `data/craft_principles.json`, `data/character_method.json` and `data/document_forms.json`, and that is what the prompts are built from.

## The order of work

A case is built in this order, and the order is the method:

1. **World before crime.** One specific institution in one specific place and time, already struggling with something ordinary before anything went wrong. It has textures, internal words staff never explain, and rhythms that stamp its paper. (CP-02; Chandler, *The Simple Art of Murder*, 1944.)
2. **People before suspects.** Every named person has a want that predates the case, an obligation that pulls against it, a habit of attention, a thing they would lie about and their reason, and a life off the page. (CP-03; McKee, *Story*, 1997; Forster, *Aspects of the Novel*, 1927.)
3. **What really happened, and why it matters.** The culprit acts for a reason a fair-minded colleague could explain. The institution then puts a cover story on paper, and most of the archive is written by people who believe it. (CP-04; Renoir's "everyone has their reasons"; Highsmith, 1966.)
4. **The shape of the revelation.** A human question the case is really about, an irony, a hook that works without the solution, and an ending note: what the truth costs. (CP-01, CP-15; P. D. James, 2009; Sayers, 1935.)
5. **The turn and the false lead.** An early, ordinary-looking fact that a later fact re-reads; a false lead caused by a real secondary secret. (CP-06, CP-07; Curran on Christie, 2009; Ohlsson on insight as re-encoding, 1992.)
6. **Only then, the cut.** List the paper trail the true events, the cover and ordinary life would leave; choose documents from it; give every document an author, a reader and a reason to exist. (CP-08.)
7. **Then the prose, one document at a time,** written by the author for the reader, about the author's own business, carrying its facts in the details that author would naturally record. (CP-09, CP-10, CP-12.)

Truth is fixed and checked before any player-facing word exists. That is what lets the prose be free without ever lying.

## What "lived in" means here

"Real" characters are not made of colourful traits. They are made of pressure and attention:

- **Pressure:** what they want, what they owe, what they stand to lose, including losses that have nothing to do with the crime. The red-herring suspect is suspicious *because* of a true, sympathetic secret.
- **Attention:** what a person notices decides what their documents record. A stores clerk counts; a night porter notes who was tired; an analyst sees what their department's bias lets them see. The reader meets people through what they noticed.
- **Paper presence:** a suspect who appears only in crime documents is a function. Each suspect turns up in several hands, including once in something mundane: a rota swap, a heating complaint, a collection for a leaving card.

The deletion test (`CT-01`) is the guard against quirk-for-quirk: delete a trait, and if no document or choice changes, it was decoration.

## What "immersive" means here

Immersion comes from the archive being plausible as an archive:

- Every document would exist if nobody ever investigated. A document that exists only to inform the player is "a clue in costume" and gets re-cut (CP-08, RUB-16).
- The institution files things its own way: by form, number, date and routine subject. Titles never conclude (CP-12).
- Departments disagree in their assessments and agree in their findings, because findings are measurements and assessments are people (CP-09).
- The world never announces: no document tells the player they are close, clever or wrong (CP-16; dev log Entries 015 and 024).
- Restraint carries weight: procedure, omission and late filing do the work spectacle would do badly (CP-14; Jackson; M. R. James).

## What "gripping" means here

Pull comes from a human question the player wants answered regardless of the puzzle (RUB-11): a person in trouble, an absence, an injustice in small print. The puzzle then makes the player earn the answer, and the answer changes what the question meant (CP-15). The S6 review scores this; the player's after-play ratings teach the seed sampler which shapes landed.

## Familiar made new

Well-worn tropes are not the enemy; unexamined ones are. Genre pleasure is repetition with a difference (Neale, 1980), and the oldest artistic move is making the familiar strange enough to be seen again (Shklovsky, 1917). So the kit lets a case **embrace** a trope on purpose. It is declared in the sealed bible with one of eight lenses from `data/trope_lenses.json`:
- the trope as the default reading the turn reframes;
- met only through procedure;
- seen by someone looking elsewhere;
- the aftermath the genre skips;
- true but beside the point;
- the metaphor made literal;
- the threat as the one being protected;
- cosmic stakes made personal.

A declared trope never trips the trope warning. An undeclared one does, because that is the accidental kind. Stock phrasing stays banned either way: the familiar thing lives in the structure, never in borrowed sentences. The seeds suggest a lens each run, and the after-play question "the familiar parts felt new" teaches the sampler which lenses land for you.

## Slop, named precisely

The ban lists (`data/ban_lists.json`) are not a style guide. They catch the specific phrases that make a document read as generated: signposting ("a chill ran down"), machine tics ("a testament to"), puzzle words inside the world ("red herring"), confessions, and stock names. One finding worth knowing: the research report's own examples of "specific, grounded names" (Elias Vance, Aris Thorne) are among the most common machine-fiction names, so they are on the list. Names come from Python-seeded pools with distinct initials and sounds instead.

## Where the engineering comes from

The kit's structure follows *Mystery Engine Design Research* (the Neurosymbolic Blueprint in the project Drive):

- **Track 3** gives the 16 aha techniques. Each is a MASKS and REFRAMES turn with a named relation (SHIFTS-WINDOW, PRESUPPOSES, INVERTS-POLARITY and so on); `patterns.json` restates them without story.
- **Track 5** gives the double-blind audit. A model from a different family solves the case cold, and a shortcut probe tries to guess from the options alone. S7 builds Gates 3 and 4 of that protocol.
- **Track 6** gives the four-axis voice and bias matrix (signature, worldview, lens, tell), the three micro-acts of pacing, archival humanity, honest short flavor items, and the eight LLM failure modes the kit's checks are mapped to.

## Where this guide's sources are weaker

Most principles above are long-settled craft (fair play, plotting backward, polyphony, restraint). Three are informed opinion rather than research: "paper has a reason to exist" (CP-08), "no quirk without cost" (CP-11) and the specific thresholds in `limits.json` (form share, world share, overlap n-grams). Treat those numbers as starting points to tune after real cases, not findings.
