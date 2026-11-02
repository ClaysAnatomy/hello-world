# Media: physical artifacts, calculated consistently

Some papers in a case should reach the player as objects rather than plain text: a photograph with a date stamp in the corner, a scanned staff badge, a page from the station bulletin, a stamped incident form, a handwritten note, a teleprinter sheet, a single video log. This layer makes those artifacts **consistent by construction**. A model decides *what* an artifact is. Python calculates *every value it shows*.

## Three laws

1. **One source of truth.** Every number, date, imprint and name an artifact shows is computed once per case, into a sealed registry, and reused everywhere. The same badge number appears on the badge, on the report that officer filed, and in the note that mentions them. No model ever invents one.
2. **Everything visible is in the text.** Each value an artifact shows must also appear, verbatim, in that document's text (KT-MD-04). Search, the transcript and the image can never disagree. A generated image may render only the text it is given (`text_in_image`), so a picture can never smuggle in a contradiction.
3. **Wear never hides evidence.** Paper ages, fades, foxes and stains according to its stock, its age, the climate and how it was kept. If the wear would push an artifact below the legibility floor (0.75), the kit scales the wear back and records that it did (`clamped`). Realism serves fairness, never the reverse.

## How values are calculated (`data/media_calculus.json`)

| Value | Rule | What it makes possible |
|---|---|---|
| Report numbers | `{inst}-{yy}-{seq}`, rising with the filing date across every report in the case; the gap between two reports grows with the days between them | A report filed later always has a higher number. A deliberate exception is evidence (see anomalies). |
| Badge numbers | `{inst}-{seq}`, issued in order of each person's issue date | Whoever joined first has the lower number. Seniority is readable from the badges. |
| Badge dates | Issued 120 days to 10 years before the archive date; expires 1,095 days after issue | Issue and expiry dates always agree with each other and with the case. |
| Newspaper issues | Issue number = days since founding ÷ cadence + 1; volume = years since founding + 1; the dateline's weekday is computed | Two clippings from the same paper agree on numbering, and every dateline has the right weekday. |
| Photo frames | Per camera, in shooting order, with a few skipped frames for shots not in the archive; film rolls wrap at 36 | Frame 14 was taken after frame 12 on the same camera. Gaps imply missing photographs. |
| Imprints | From the camera kind: film prints `'26 3 4`, digital prints date and time, CCTV prints camera, date and seconds | A camera never prints in the wrong style, and a time only appears where the plan gave one. |
| Message numbers | `{inst}/{day of year}/{seq}`, restarting daily and rising through the day; the date-time group is `DDHHMMZ MON YY` | Teleprinter traffic reads like a real log. |
| Charts, specimens, drawings, tapes, terminals | Their own series, each rising with time | Every catalogued thing has a number that fits its date. |
| Light | From climate, hemisphere, month and hour: polar night, midnight sun, a low short day, or ordinary day and night | A photograph taken at a polar station in December shows no daylight, and the writer is told so. |
| Surface | Yellowing, ink fade, foxing, creases, edge wear, stains and scan skew, from stock, age, climate, handling (0 to 5) and storage (filed, boxed, pinned, pocket, framed) | The Desk and the image generator draw the same paper. Newsprint yellows in a few years; bond takes decades; thermal fax paper fades. |

Every random-looking value comes from a stable hash of the case's seeds, so the same case always produces the same registry, and a different case produces different numbers.

## The artifact forms (`data/media_forms.json`)

Twelve forms, each with its regions. A region is calculated by the kit (`registry`), typed or handwritten by the author in S3 (`prose`, `handwriting`), a plain description of what an image shows (`depiction`), or a picture (`image`).

| ID | Form | Dresses | Needs an image |
|---|---|---|---|
| MF-01 | Photograph print | DF-17 | yes (photo) |
| MF-02 | Instant photograph | DF-17, DF-06 | yes (photo) |
| MF-03 | Identity badge scan | DF-19, DF-10 | yes (portrait) |
| MF-04 | Newspaper page or clipping | DF-18 | no: the Desk typesets it |
| MF-05 | Incident or arrest report form | DF-01, DF-19, DF-13 | no |
| MF-06 | Handwritten letter or note, scanned | DF-06, DF-12, DF-15, DF-16 | yes (handwriting) |
| MF-07 | Teleprinter or fax printout | DF-07, DF-09, DF-20, DF-15 | no |
| MF-08 | Instrument chart or strip record | DF-04, DF-14 | no: the Desk draws it |
| MF-09 | Annotated plan or map | DF-18, DF-04 | no: the Desk draws it |
| MF-10 | Terminal screen capture | DF-10, DF-11, DF-04 | no |
| MF-11 | Label, tag or specimen card | DF-11, DF-20 | no |
| MF-12 | Video log (at most one per case) | DF-09, DF-16, DF-12 | video brief |

## Where it happens

| Stage | What happens |
|---|---|
| S1 | Every person gets an `appearance`: fixed physical details an artist could draw the same way every time. |
| S2 | The plan dresses chosen documents with `media` and adds a `media_environment` (climate, hemisphere, cameras, publications). Checks KT-MD-01, 02, 03, 07, 08 and 09. When S2 is accepted, Python builds `checkpoints/media_registry.json`, which stays sealed. |
| S3 | A media document's brief gains **The object**: the printed values to copy exactly, how to write a depiction (only what a camera could see), and the light at the time. Checks KT-MD-04, 05 and 06. |
| S3 gate | KT-MD-05 and 06 run across every document, so no paper invents a series number or writes a wrong weekday. |
| Finish | Python writes `media_manifest.json` next to the case and prints `MEDIA artifacts n plates n video n`. |

## Outputs

- **`checkpoints/media_registry.json`** (sealed). The full calculation, including which values are deliberate anomalies. Never shown to the player or to any later model.
- **`media_manifest.json`** (player-safe). For each artifact: form, aspect, regions (registry text, or the JSON path of the prose in the case), surface values, plate ID, and alt text (the depiction). It contains nothing the player will not see anyway: no facts, roles, tiers, routes or anomaly flags (tested).
- **Plates**, inside the manifest. One brief per artifact that needs a generated image: kind, aspect, era, camera, light, climate, each subject's name and likeness, places by name, the depiction, the exact `text_in_image`, the rules, the surface values and a stable seed. The same person carries the same likeness text in every plate.

## Anomalies

Sometimes an inconsistency *is* the clue: a report number out of sequence, a backdated stamp. The plan may declare one `anomaly` per artifact: which value, what it shows instead, and the fact it carries. The kit checks that it really differs from the calculation (KT-MD-08), uses it in the registry, and accepts it in the lint. An undeclared inconsistency is always an error. The manifest never reveals which values are anomalies.

## Non-clue papers are never padding (KT-PL-18)

Every world document declares a `purpose`:
- `teaches_rule` names one of the setting's internal terms;
- `character_dynamic` names at least two people who appear in it;
- `setting_mechanic` establishes a routine, constraint or piece of equipment.

Each comes with a one-line note.

## Video

The design calls for exactly one prestige video log per case. `limits.json` → `media.video` holds `max: 1`, `min: 1` and `min_enforced: false`. Until the video pipeline exists, a case may have none, and never more than one. Set `min_enforced` to true when video generation is ready.

## Not built yet

- Generating the plate images (Gemini) and the video. The plate brief format is ready for them.
- The Desk renderer for artifacts (the chassis lane). It should read `media_manifest.json` and draw each form from its regions and surface values, the same way every time.
- Audio.
