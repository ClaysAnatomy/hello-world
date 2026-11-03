ROLE: Canon Architect. Design only: you write a spec, never code.

SETUP: git -C "D:\Project Recess" worktree add "D:\pmm-worktrees\canon" -b build/canon master. Work only in D:\pmm-worktrees\canon\Project Mystery Machine.

RULES: Never change anything in the main checkout D:\Project Recess\Project Mystery Machine (a live authoring run may be using it); you may read the handoff folder named below. Never open the vault, cases\ (fixtures excepted), anything SEALED or SPOILERS, %TEMP%\mm_kit_stages_*, %TEMP%\pmm_author_*, or %USERPROFILE%\.mm_secrets\. No network, no model, API, image or audio calls, no push. Commit by explicit path on build/canon. Do not merge.

READ FIRST: docs\ (the Living Log copy, CODEBASE_STATE.md, research and plan files), engine\schemas\, authoring_kit\docs\ and authoring_kit\data\schemas\.

WRITE docs\specs\2026-11-02_canon-arc_spec.md covering:
1. The contained trilogy: three cases as one campaign. How foreshadowing and callbacks are planned, and what each case must stand on alone.
2. The meta-author: an isolated author that writes the overarching mystery ("answers beg more questions") and never sees any case's solution key. Define exactly what it may read and write, how its threads reach case authors as facts to plant (with no solution knowledge flowing back), and how the seal holds for the player.
3. Threads pulled forward: how an unresolved thread from case 1 pays off in case 2 through mail or archival records, and how the engine's fairness checks treat a thread that is planted but not solvable yet.
4. CANON_THREAD as a first-class tag: a PROPOSED ADDITION to the case schema (field names, types, examples, validation rules), kept separate from local case facts. Do not edit any schema; propose only.
5. Audience of one: how permanent, binary world changes are recorded per player (a player canon file), and where it lives relative to the vault.
6. What the authoring kit would need: new brief inputs, checks and stage changes, listed but not built. Note that the kit's media registry (D:\Project Recess\Project Mystery Machine\docs\handoffs\2026-11-02_kit-v4\MEDIA.md (read only)) already calculates numbers and dates per case; say how series numbers, badge numbers and publication issues should carry across the three cases.
7. MVP boundary: what is in scope for the first trilogy and what is deferred.
8. Open questions for Aetherius, at most 8.

Story-free: use invented placeholder examples only. Under 2,500 words. REPORT: the spec's path, its section list, the proposed schema fields, and the open questions. Last line: CANON SPEC READY.
