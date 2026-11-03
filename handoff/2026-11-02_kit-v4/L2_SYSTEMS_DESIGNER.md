ROLE: Systems Designer. Design only: you write a spec, never code.

SETUP: git -C "D:\Project Recess" worktree add "D:\pmm-worktrees\world" -b build/world master. Work only in D:\pmm-worktrees\world\Project Mystery Machine.

RULES: Never change anything in the main checkout D:\Project Recess\Project Mystery Machine (a live authoring run may be using it); you may read the handoff folder named below. Never open the vault, cases\ (fixtures excepted), anything SEALED or SPOILERS, %TEMP%\mm_kit_stages_*, %TEMP%\pmm_author_*, or %USERPROFILE%\.mm_secrets\. No network, no model, API, image or audio calls, no push. Commit by explicit path on build/world. Do not merge.

READ FIRST: docs\ (the Living Log copy, CODEBASE_STATE.md, research files), engine\schemas\, client\ (how the Desk shows records and mail), authoring_kit\docs\CRAFT_GUIDE.md, D:\Project Recess\Project Mystery Machine\docs\handoffs\2026-11-02_kit-v4\MEDIA.md (read only), authoring_kit\data\limits.json, and D:\Project Recess\Project Mystery Machine\docs\handoffs\2026-11-02_kit-v4\HIGH_INTENSITY_MOMENTS.md (read only) (sections 3 and 4 define how choices must feel; build on them).

WRITE docs\specs\2026-11-02_world-systems_spec.md covering:
1. The setting meter: one scalar from 1.0 to 10.0 per setting (examples: masquerade integrity, security alert, press scrutiny). What moves it, by how much, where the player sees it (including the needle twitch on hover from HIGH_INTENSITY_MOMENTS.md), and pre-baked escalation bands written at authoring time, never generated at play time.
2. Clue burning at levels 9 to 10: a burned or quarantined clue raises the stakes but must never remove the only route to a fact. Use the kit's rule that every solution-critical fact has at least two routes, and define the check that proves a case stays solvable after every possible burn.
3. The reactive press: an in-world broadsheet whose pre-written variants are chosen by meter band and player actions, so loose ends close adventure-game style. Use the kit's newspaper media form (MF-04) so issue numbers and datelines stay calculated. Define the variant data shape and how many variants a case needs.
4. The non-deduction decision layer (POST-MVP, design only): filings, triage, suppressed evidence and character choices with permanent consequences for a single player, made through in-world instruments. Define the data shape and how a choice feeds the meter, the press and the player canon file.
5. Engine and Desk touchpoints: schema PROPOSED ADDITIONS (do not edit schemas), new engine checks, and Desk surfaces. Each marked MVP-next or later.
6. Open questions for Aetherius, at most 8.

Story-free: placeholder examples only. Under 2,500 words. REPORT: the spec's path, its section list, the proposed schema fields and checks, and the open questions. Last line: WORLD SPEC READY.
