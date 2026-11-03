# The two highest-intensity moments: filing the deduction, and making a choice

A design for the Desk and the kit. Story-free. It covers the final deduction (the moment you commit to who did it and why) and the choice moments (permanent decisions outside the deduction). Everything else in the game supports these two moments, so they get a deliberate design language: their own visuals, sound, pacing and fiction.

The aim, in one line: **filing should feel like signing your name to something true, and a choice should feel like something you can't take back.**

---

## 1. What the research says, and what we take from it

| Source | Finding | What we take |
|---|---|---|
| Kahneman, Fredrickson, Schreiber and Redelmeier (1993), *When more pain is preferred to less*; Fredrickson and Kahneman (1993), *Duration neglect in retrospective evaluations* | People remember an experience mostly by its most intense moment and its end, not its length (the peak-end rule). | The filing is the peak and the epilogue is the end. Together they decide how the whole case is remembered, so they get the most design care. Never end on a score screen. |
| Kivetz, Urminsky and Zheng (2006), *The goal-gradient hypothesis resurrected* | Effort and attention rise as a goal gets closer. | Build visible approach: the docket fills as the player pins evidence, so the last steps feel heavier and more deliberate. |
| Norton, Mochon and Ariely (2012), *The IKEA effect* | People value what they built themselves more highly. | The player *assembles* the argument (claim plus pinned evidence) rather than ticking a box. The verdict judges something they made. |
| *Return of the Obra Dinn* (Lucas Pope, 2018) | Fates are confirmed only in sets of three correct answers, which stops guessing and makes each confirmation an event. | Feedback is withheld until the whole docket is filed, and confirmation is ceremonial. |
| *The Case of the Golden Idol* (Color Gray Games, 2022) | Deductions are sentences the player completes from collected words; the answer is accepted only when the whole sentence is right. | The docket reads as a sentence the player writes: "*[name]* did it, because *[evidence]*". |
| *Papers, Please* (Lucas Pope, 2013) | The decision is a physical act (the stamp), and its consequences arrive later in the morning paper. | Choices are made with in-world instruments, and consequences arrive diegetically and late. This is the reactive press. |
| *Disco Elysium* (ZA/UM, 2019) | Red checks can be attempted only once, and the game marks them so you know before you try. | Irreversible acts get a reserved visual signal, shown *before* the act. |
| *Her Story* (Sam Barlow, 2015) | The player decides when they know enough. | The Desk never says "you are ready". Filing is always available; the weight comes from the player's own judgement. |
| Toulmin, *The Uses of Argument* (1958) | An argument is a claim backed by grounds (evidence) and a warrant (why the evidence supports it). | The docket asks for the claim and the grounds. The reveal supplies the warrant, showing *why* the pinned evidence proves it. |
| GUMSHOE (Robin D. Laws, 2007) | Core clues are always found; the challenge is interpretation, not discovery. | Already built: every fact has two routes. So a wrong filing is a failure of reasoning, never of luck, and the reveal can show the route the player missed. |

---

## 2. The final deduction: filing the docket

### 2.1 The fiction
The deduction is a real document in the world: the form the investigator sends up the chain. At the arctic station, that's a **Station Incident Return**, transmitted by telex at the next radio window. Every setting gets its own: a coroner's return, a commission's finding, a ward report. The skin names it and styles it.

### 2.2 The sequence (six beats)

1. **Open the docket.** The Desk shifts register: the room dims to a pool of lamp light around the form, ambient sound thins, and the typography changes to the institution's form face. Everything else on the Desk stays reachable, but visually recedes.
2. **Write the sentence.** For each question, the player picks an answer *and pins evidence to it*, dragging records onto the claim the way you'd clip papers to a file. The form reads as prose as it fills: "*Name* entered the pumproom at 14:30, as shown by …". The approach is visible: a margin tally of questions answered and evidence pinned. No hints, and no "ready" signal.
3. **Review.** One calm read-through of the whole return, in the form's own layout. This is the last chance to change anything, and the Desk says so plainly.
4. **Commit.** **Press and hold** the seal or stamp: about 1.2 seconds, with a rising sound and the stamp's shadow pressing down. Releasing early cancels. This is the only press-and-hold in the game, so it carries meaning by rarity. The ink is **red**: the one colour reserved, everywhere in the game, for irreversible acts. Keyboard: hold Enter. Reduced motion: a two-step confirm with the same sound.
5. **The wait.** The return is transmitted. A short sealed interval follows: the teleprinter chatters, the radio window opens, the room tone comes back. That's 6 to 12 seconds of held suspense, never longer, and skippable after the first case. Suspense needs uncertainty about an outcome that matters, and both are at their highest here.
6. **The answer arrives as a document.** The verdict is never a popup. It arrives in the world: a telex from the mainland, a letter from the commissioner, a call slip. It reads in the voice of the institution. Then the reveal begins.

### 2.3 The reveal: show the reasoning, not just the score
- **One question at a time, building to the peak.** Order runs from least to most significant, with the culprit last.
- **Evidence replay.** For each question, the Desk reopens the record that decides it and lights up the passage that carries the deciding fact. The kit already knows which text asserts which fact: `claims.json` maps every field to the facts it carries. The highlight therefore shows *why*, the Toulmin warrant, in the archive's own words.
- **Credit for reasoning.** If the player pinned evidence that genuinely establishes the answer, the reveal says so: "You cited the 14:30 log; that is what places her there." This uses the same scorer as the blind audit (every pinned record valid, and together covering the supporting facts). The right name with the wrong evidence reads differently from a sound argument: "The name is right. The return would not have held."
- **The route you missed.** When the player is wrong, the reveal shows the cheapest route they didn't take: two documents, side by side, and the line in each. Because every fact has two routes, there's always one to show.

### 2.4 The end (the "end" of peak-end)
- **The world reacts.** A short epilogue in diegetic media: the reactive press clipping, a last telex, a letter. It's keyed to the outcome band: right with sound reasoning, right with thin reasoning, partly right, or wrong.
- **Failure is a story, never a dead end.** A wrong filing has consequences in the fiction (the wrong person is suspended, the bulletin runs the wrong story), and the truth still surfaces in the epilogue, or is held for the trilogy's canon thread.
- **The last image is quiet.** The lamp clicks off over the filed return. No score screen. A small "your record" ledger (cases filed, reasoning held) lives in a drawer for anyone who wants it.

---

## 3. Choice moments: decisions outside the deduction

The decision layer is post-MVP, so this section is design only, ready for the world-systems spec.

### 3.1 Principles
1. **Every choice is an act with an instrument.** You don't click "Option B". You stamp a form, sign a release, redact a line with a marker, seal an envelope, forward a telex, or feed a page to the stove. Each instrument has its own gesture and sound, so the player's body learns the vocabulary.
2. **Few, and each one permanent.** One to three choices per case. Each is irreversible and recorded in the player's canon file. Scarcity makes them weigh.
3. **The stakes are visible; the outcome is not.** Before acting, the player sees what a choice touches. Hovering an instrument makes the setting meter's needle twitch toward its likely direction, and the cost line reads in the fiction ("This telex goes to the mainland"). They never see the result.
4. **Every option costs something and protects someone.** The design rule for writers: no free option, and no obviously right one. Truth against protection, containment against disclosure, a colleague against the institution.
5. **Deadlines are diegetic, never a clock.** "The courier leaves at the 06:00 window" means a choice must be made before a certain document is opened, or before the case is filed. This respects reading pace.
6. **Consequences arrive late and in the world.** As in *Papers, Please*: the next mail drop, the bulletin, or the next case of the trilogy. Never an immediate popup.

### 3.2 The choice sequence (four beats)
1. **The instrument is presented,** in red-reserved framing: a red wax tab or a red rule on the form. The player knows before they act that this can't be undone.
2. **Consider.** The meter twitches on hover, and the cost line shows. The player can leave and come back.
3. **Act** with the instrument's own gesture: hold to stamp, drag the marker across the line, drag the page into the stove.
4. **Settle.** A brief, specific aftermath in the room: the stove flares and the page curls, or the envelope drops into the outbox. Then normal register returns. The consequence comes later.

---

## 4. The design language for both moments

| Channel | Ordinary play | High-intensity moments |
|---|---|---|
| Colour | The skin's palette | Red ink appears **only** for irreversible acts, anywhere in the game; the room desaturates slightly around the moment |
| Light | Even desk light | A lamp pool, with a vignette on the rest of the Desk |
| Type | The skin's reading faces | The institution's form face; stamps in a slab or condensed face |
| Motion | Quick: 120 to 200 ms | Slow and weighted: 300 to 600 ms ease-out, so the contrast makes these moments feel heavy |
| Sound | Room tone and paper | Room tone drops away; single foley (pen, stamp, seal); a held silence before the verdict; then the verdict's own arrival sound (teleprinter, pneumatic tube, letterbox) |
| Input | Click and drag | Press-and-hold for commit, used nowhere else; instrument gestures for choices |
| Accessibility | | Every hold has a keyboard equivalent; `prefers-reduced-motion` swaps motion for a two-step confirm; every sound has a caption |

---

## 5. What the kit and engine need

Built already:
- **Two routes per fact,** so a missed route can always be shown.
- **`claims.json`,** the map from each field to the facts it asserts, so evidence replay can highlight the deciding passage.
- **The audit scorer** (precision plus coverage), reusable to judge the player's pinned evidence.
- **The media layer,** so verdicts and epilogues can arrive as telexes, letters and clippings with consistent numbering and dates.

To build next, in proposed order:
1. **Desk: the docket.** Pinning evidence to answers; press-and-hold red-ink filing; one irreversible filing per case, stored in the player's canon file.
2. **Desk: the reveal.** Question-by-question reveal ending on the culprit, with evidence replay from `claims.json` and the missed-route view.
3. **Kit: verdict and epilogue texts.** A new sealed stage after S4, written by an author who may see the bible (the reveal must tell the truth). It writes one verdict document per question band and one epilogue per outcome band, dressed with media forms. These are sealed until the player files.
4. **Kit and engine: a docket schema.** The player's answers and pinned record IDs, scored by the audit scorer.
5. **Later, with the world-systems spec:** choice instruments, the meter twitch, and the reactive press variants.

---

## 6. The first case: arctic station

- **The docket** is a Station Incident Return, typed on the station's form and transmitted by telex.
- **The wait** is the radio window: the teleprinter warms, the carrier tone holds, and then the mainland's reply chatters out line by line. That is MF-07, with a real message number and date-time group from the media registry.
- **The verdict** arrives as that telex. The epilogue is the next supply flight's mail bag: a clipping from the station bulletin (MF-04), and one letter.
- **A choice, if the decision layer is on:** what to transmit and what to hold back. The stove is the instrument for anything burned.
- **The last image:** the lamp goes off, and the polar night stays outside the window, because the media registry already knows it's polar night.

---

## 7. How we'll know it works

Add to the feedback form after each case:
1. "How did filing feel?" (weightless / considered / heavy / dreadful)
2. "Did the reveal show that your reasoning mattered?" (yes / partly / no)
3. "Which moment do you remember most?" (free text)
4. "Did the ending feel like an ending?" (yes / no)

Questions 1 and 4 measure the peak and the end directly.
