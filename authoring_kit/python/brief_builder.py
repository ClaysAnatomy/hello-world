"""brief_builder: fill prompt templates from data and prepare stage folders.

A stage folder holds prompt.md, unit.json and inputs/ with only the files that
stage may read. S3 folders hold one document's brief and no case files, so the
answer key cannot leak into document prose. Nothing here prints any brief.
"""
from __future__ import annotations

import re
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402
import media as MD  # noqa: E402

TOKEN_RX = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

MARKER = ".mm_kit_stage_root"


def _fresh_dir(sdir: Path) -> None:
    """Empty a stage folder, refusing to delete anything outside a marked stage root."""
    if sdir.exists():
        if not (sdir.parent / MARKER).is_file():
            raise K.KitError("ERR_STAGE_ROOT_IN_WS", code=2)
        shutil.rmtree(sdir)
    (sdir / "inputs").mkdir(parents=True)



def render(template: str, ctx: dict[str, str]) -> str:
    missing = sorted({m for m in TOKEN_RX.findall(template) if m not in ctx})
    if missing:
        raise K.KitError("ERR_TEMPLATE_TOKEN", code=2)
    return TOKEN_RX.sub(lambda m: str(ctx[m.group(1)]), template)


def _by_id(items: list[dict]) -> dict[str, dict]:
    return {it["id"]: it for it in items}


def _bullets(lines: list[str]) -> str:
    return "\n".join(f"- {ln}" for ln in lines) if lines else "- none"


# ---------------------------------------------------------------- shared blocks

def ban_summary() -> str:
    lines = []
    for cat in K.data("ban_lists")["categories"]:
        if cat["applies_to"] in ("fills", "fills_and_bible"):
            sev = "never" if cat["severity"] == "ERROR" else "avoid"
            lines.append(f"{cat['id']} ({sev}): " + "; ".join(cat["terms"]))
    return _bullets(lines)


def header() -> str:
    return render((K.PROMPTS_DIR / "header_sealed.md").read_text(encoding="utf-8"), {"BAN_SUMMARY": ban_summary()})


def check_list(stage: str) -> str:
    cat = K.data("check_catalog")["checks"]
    prefixes = {"S1": ("KT-BI-",), "S2A": ("KT-PL-",), "S3": ("KT-FL-", "VL-"), "S4": ("KT-FL-", "VL-"),
                "S6": ("KT-RV-",)}.get(stage, ())
    skip = {"S3": {"VL-04", "VL-05"}, "S4": {"VL-07", "VL-08", "VL-09"}}.get(stage, set())
    extra = {"S2A": {"KT-MD-01", "KT-MD-02", "KT-MD-03", "KT-MD-07", "KT-MD-08", "KT-MD-09"},
             "S2B": {"KT-PL-01", "KT-PL-10", "KT-PL-12", "KT-PL-14"},
             "S3": {"KT-MD-04", "KT-MD-05", "KT-MD-06"}, "S4": {"KT-MD-05", "KT-MD-06"}}.get(stage, set())
    return _bullets([f"{cid}: {txt}" for cid, txt in cat.items()
                     if (cid.startswith(prefixes) and cid not in skip) or cid in extra
                     or (cid.startswith("KT-IO-") and (stage == "S1" or cid != "KT-IO-03"))])


def turn_budget(stage: str, target_stage: str | None = None) -> str:
    """One sentence telling the agent how many turns it has. Every tool call is a turn."""
    t = K.data("limits")["turns"]
    if stage == "S5" and target_stage in t.get("repair_unit_caps", {}):
        n = t["repair_unit_caps"][target_stage]
    else:
        n = t["unit_caps"][stage]
    return (f"You have at most {n} turns, and every tool call (each read and each write) uses one. "
            "Every input is already written out in full at the end of this brief, so do not read any file: "
            "plan, then write each output whole in a single write. "
            "When the turns run out you are stopped mid-task and nothing unfinished counts.")


def limits_text() -> str:
    lim = K.data("limits")
    b, w, p = lim["budget"], lim["world"], lim["people"]
    return _bullets([
        f"Suspects: {b['min_suspects']} to {b['max_suspects']}. Named people in total: at most {b['max_cast_total']}.",
        f"Locations: at most {b['max_locations']}. Critical times or codes: at most {b['max_critical_strings']}.",
        f"Departments: at most {b['max_departments']}.",
        f"Relationships per person: at least {p['min_relationships_per_person']}.",
        f"Distinct document forms: at least {w['min_distinct_forms']}; no form above {int(w['max_form_share'] * 100)} percent of documents.",
        f"World documents: {int(w['world_clue_share_min'] * 100)} to {int(w['world_clue_share_max'] * 100)} percent of documents.",
    ])


def capability_terms(compat: dict) -> str:
    lines = []
    for cap in K.data("capability_map")["capabilities"]:
        term = compat.get("capabilities", {}).get(cap["id"])
        lines.append(f"{cap['label']}: {term if term else 'not available in this engine'}")
    return _bullets(lines)


def seeds_table(seeds: dict) -> str:
    sd = K.data("story_seeds")
    pick = lambda key, sid: _by_id(sd[key])[sid]["text"]  # noqa: E731
    pats = _by_id(K.data("patterns")["patterns"])
    lines = [
        "Aha patterns: " + "; ".join(f"{p} {pats[p]['name']}" for p in seeds["patterns"]),
        f"Mechanism {seeds['mechanism']}: {pick('mechanisms', seeds['mechanism'])}",
        f"False-lead type {seeds['red_herring']}: {pick('red_herrings', seeds['red_herring'])}",
        f"Stakes {seeds['stakes']}: {pick('stakes', seeds['stakes'])}",
        f"Human question {seeds['human_question']}: {pick('human_questions', seeds['human_question'])}",
        f"Irony {seeds['irony']}: {pick('ironies', seeds['irony'])}",
        f"Setting texture {seeds['setting_texture']} (used only where the brief is silent): {pick('setting_textures', seeds['setting_texture'])}",
        f"Suspects: {seeds['suspect_count']}. Named people in total: {seeds['cast_total']}. Locations: about {seeds['location_count']}.",
        "Cast names (assign each to one person and spell exactly; replace a name only if the brief's setting needs another naming culture, keeping every initial and sound distinct): " + "; ".join(f"{n['given']} {n['family']}" for n in seeds["cast_names"]),
        "Critical strings (use exactly; give each a meaning): " + "; ".join(f"{c['id']} = {c['value']}" for c in seeds["critical_strings"]),
    ]
    if seeds.get("lens_hint"):
        ln = _by_id(K.data("trope_lenses")["lenses"]).get(seeds["lens_hint"])
        if ln:
            lines.append(f"Lens to try first if the story embraces a familiar trope, {ln['id']}: {ln['name']}")
    return _bullets(lines)


def pattern_briefs(seeds: dict) -> str:
    pats = _by_id(K.data("patterns")["patterns"])
    forms = _by_id(K.data("document_forms")["forms"])
    blocks = []
    for pid in seeds["patterns"]:
        p = pats[pid]
        blocks.append("\n".join([
            f"### {pid} {p['name']}",
            f"Mechanism: {p['mechanism']}",
            *([f"Engine name for this pattern: {p['engine_aha']} (use it wherever the engine records the aha pattern)."]
              if p.get("engine_aha") else []),
            "Plant early:",
            _bullets(p["presignal"]),
            f"How it fails: {p['failure_mode']}",
            "Forms that host it well: " + ", ".join(f"{f} {forms[f]['name']}" for f in p["good_forms"]),
        ]))
    return "\n\n".join(blocks)


def trope_lenses() -> str:
    rows = ["| ID | Lens | The move | Watch for |", "|---|---|---|---|"]
    for ln in K.data("trope_lenses")["lenses"]:
        rows.append(f"| {ln['id']} | {ln['name']} | {ln['move']} | {ln['risk']} |")
    return "\n".join(rows)


def person_sheet() -> str:
    cm = K.data("character_method")
    return _bullets([f"`{s['field']}`: {s['ask']}" for s in cm["sheet"]]) + "\n\nAvoid:\n" + _bullets(cm["avoid"])


def person_tests() -> str:
    return _bullets([f"{t['id']} {t['name']}: {t['ask']}" for t in K.data("character_method")["tests"]])


def forms_table() -> str:
    rows = ["| ID | Form | Exists to | Reveals | Hides | Voice |", "|---|---|---|---|---|---|"]
    for f in K.data("document_forms")["forms"]:
        rows.append(f"| {f['id']} | {f['name']} | {f['purpose']} | {f['reveals']} | {f['hides']} | {f['voice_tip']} |")
    return "\n".join(rows)


def techniques_table() -> str:
    rows = ["| ID | Technique | Use | Risk |", "|---|---|---|---|"]
    for t in K.data("document_forms")["techniques"]:
        rows.append(f"| {t['id']} | {t['name']} | {t['use']} | {t['risk']} |")
    return "\n".join(rows)


def voice_profile_text(p: dict) -> str:
    vm = K.data("voice_matrix")
    axes = {a["id"]: a["name"] for a in vm["axes"]}
    r = p["rules"]
    return "\n".join([
        f"Voice {p['id']}: " + "; ".join(f"{axes[k]} {v}" for k, v in p["position"].items()) + ".",
        f"Bias: {p['bias']}",
        f"Assessment sentences average {r['assessment_sentence_words'][0]} to {r['assessment_sentence_words'][1]} words. "
        f"First person: {r['first_person'].replace('_', ' ')}. Hedging: {r['hedges']}.",
        "Each assessment uses at least one of: " + "; ".join(r["required_in_assessment_any"]) + ".",
        "Syntax examples (nonsense content, copy the shape only):",
        _bullets(p["exemplars"]),
    ])


def voice_slots(seeds: dict) -> str:
    profiles = _by_id(K.data("voice_matrix")["profiles"])
    return "\n\n".join(f"Slot {i + 1}:\n{voice_profile_text(profiles[v])}" for i, v in enumerate(seeds["dept_mix"]))


def world_brief(bible: dict) -> str:
    st = bible["premise"]["setting"]
    return _bullets([
        f"Place: {st['place']}. Institution: {st['institution']}. Era: {st['era']}.",
        f"What the place was already struggling with: {st['before_problem']}",
        "Texture: " + "; ".join(st["texture"]),
        "Internal terms: " + "; ".join(f"{t['term']} ({t['meaning']})" for t in st["internal_terms"]),
        "Rhythms: " + "; ".join(st["rhythms"]),
    ])


def cast_names(bible: dict) -> str:
    return _bullets([f"{c['id']}: {c['name']['given']} {c['name']['family']}" for c in bible["cast"]]
                    + [f"{l['id']}: {l['name']}" for l in bible["locations"]])


def facts_table(fact_ids: list[str], bible: dict) -> str:
    facts = _by_id(bible["facts"])
    return _bullets([f"{fid}: {facts[fid]['statement']}" for fid in sorted(set(fact_ids)) if fid in facts])


def slots_table(phs: list[dict], bible: dict) -> str:
    crit = {c["id"]: c["value"] for c in bible["critical_strings"]}
    dflt = K.data("limits")["prose"]["default_max_words"]
    rows = ["| Token | Field | Kind | Max words | Facts | Must contain |", "|---|---|---|---|---|---|"]
    for ph in phs:
        req = ", ".join(f"{cs} `{crit.get(cs, '')}`" for cs in ph["required_strings"]) or "-"
        rows.append(f"| {ph['token']} | {ph['slot']} | {ph['kind']} | {ph.get('max_words', dflt)} | {', '.join(ph['facts']) or '-'} | {req} |")
    return "\n".join(rows)


def required_strings(phs: list[dict], bible: dict) -> str:
    crit = {c["id"]: c["value"] for c in bible["critical_strings"]}
    lines = [f"`{crit[cs]}` in {ph['token']}" for ph in phs for cs in ph["required_strings"] if cs in crit]
    return _bullets(lines)


def _io(inputs: list[tuple[str, str]], outputs: list[tuple[str, str]]) -> tuple[str, str]:
    return (_bullets([f"`{p}`: {d}" for p, d in inputs]), _bullets([f"`{p}`: {d}" for p, d in outputs]))


# ---------------------------------------------------------------- stage preparation

def _engine_path(root: Path, rel: str) -> Path:
    p = root / rel
    if not p.is_file():
        raise K.KitError("ERR_ENGINE_FILE_MISSING", code=2)
    return p


def _inline_text(p: Path) -> str:
    raw = p.read_text(encoding="utf-8-sig")
    if p.suffix == ".json":
        try:
            return json.dumps(json.loads(raw), ensure_ascii=False, separators=(",", ":"))
        except ValueError:
            return raw
    return raw


def inline_section(sdir: Path, rels: list[str], title: str = "Inputs, in full") -> str:
    """Every input written into the prompt, so the agent spends no turns reading files.

    JSON is minified. Files that would push the section past inline_max_chars stay as files to read.
    """
    sp = K.data("stage_plan")
    if not sp.get("inline_inputs", False) or not rels:
        return ""
    cap = int(sp.get("inline_max_chars", 600000))
    blocks, used, skipped = [], 0, []
    for rel in rels:
        p = sdir / rel
        if not p.is_file():
            continue
        body = _inline_text(p)
        if used + len(body) > cap:
            skipped.append(rel)
            continue
        used += len(body)
        fence = "~~~~" if "```" in body else "```"
        blocks.append(f"### `{rel}`\n{fence}\n{body}\n{fence}")
    out = f"\n\n## {title}\nThese are the files listed above, complete. Use them from here; do not read the files.\n\n"
    out += "\n\n".join(blocks)
    if skipped:
        out += "\n\nToo large to include here, read from disk if needed: " + ", ".join(f"`{r}`" for r in skipped)
    return out + "\n"


def prepare(unit: dict, ws: Path, root: Path, state: dict) -> Path:
    """Create the stage folder for a unit and return its prompt path.

    unit: {"unit": id, "stage": S1..S6, "owner": optional, "target": optional, "round": optional}
    """
    cfg = K.data("kit_config")
    cp = ws / "checkpoints"
    stage = unit["stage"]
    sdir = Path(state["stage_root"]) / unit["unit"]
    _fresh_dir(sdir)
    seeds = K.load_json(cp / "seeds.json")
    compat = K.load_json(cp / "compat.json")
    eng = cfg["engine"]
    ctx: dict[str, str] = {"HEADER": header(), "STAGE_ID": stage, "CHECK_LIST": check_list(stage),
                           "LIMITS_TEXT": limits_text(), "CAPABILITY_TERMS": capability_terms(compat)}
    inputs: list[tuple[str, str]] = []
    outputs: list[tuple[str, str]] = []

    def put(rel: str, src: Path | None = None, obj=None, desc: str = ""):
        dst = sdir / "inputs" / rel
        if obj is not None:
            K.dump_json(obj, dst)
        else:
            K.copy_file(src, dst)
        inputs.append((f"inputs/{rel}", desc))

    if stage == "S5":
        return _prepare_repair(unit, ws, root, state, sdir)

    lim = K.data("limits")
    if stage == "S1":
        brief = cp / "brief.md"
        if brief.is_file():
            put("brief.md", brief, desc="the request for this case, in the user's words")
            ctx["BRIEF_STATUS"] = "A brief is in `inputs/brief.md`. Read it first."
        else:
            ctx["BRIEF_STATUS"] = "No brief was given. Build everything from the seeds."
        put("README_AUTHORING.md", _engine_path(root, eng["authoring_readme"]), desc="the authoring contract")
        put("bible.schema.json", K.SCHEMA_DIR / "bible.schema.json", desc="the shape of your output")
        ctx.update({"SEEDS_TABLE": seeds_table(seeds), "PATTERN_BRIEFS": pattern_briefs(seeds),
                    "TROPE_LENSES": trope_lenses(),
                    "MAX_TROPES": str(lim.get("tropes", {}).get("max_embraced", 3)),
                    "PERSON_SHEET": person_sheet(), "PERSON_TESTS": person_tests(),
                    "MIN_TEXTURE": str(lim["world"]["min_setting_texture"]),
                    "MIN_TERMS": str(lim["world"]["min_internal_terms"]),
                    "MIN_RHYTHMS": str(lim["world"]["min_rhythms"]),
                    "MIN_RELATIONSHIPS": str(lim["people"]["min_relationships_per_person"]),
                    "MIN_SUSPECTS": str(lim["budget"]["min_suspects"]),
                    "MAX_SUSPECTS": str(lim["budget"]["max_suspects"]),
                    "AUTHORING_README": "`inputs/README_AUTHORING.md`"})
        for part in K.data("stage_plan")["bible_parts"]:
            outputs.append((part["file"], part["desc"]))
        ctx["TURN_BUDGET"] = turn_budget("S1")

    elif stage == "S2A":
        put("bible.json", cp / "bible.json", desc="the sealed story and truth bible")
        put("README_AUTHORING.md", _engine_path(root, eng["authoring_readme"]), desc="the authoring contract")
        put("clue_plan.schema.json", K.SCHEMA_DIR / "clue_plan.schema.json", desc="the shape of the plan")
        p = lim["people"]
        w = lim["world"]
        ctx.update({"VOICE_SLOTS": voice_slots(seeds), "FORMS_TABLE": forms_table(),
                    "MEDIA_FORMS_TABLE": MD.forms_table(), "MEDIA_LIMITS": MD.limits_text(),
                    "TECHNIQUES_TABLE": techniques_table(),
                    "PLACEHOLDER_FORMAT": lim["ids"]["placeholder_format"],
                    "S4_OWNER": K.data("stage_plan")["s4_owner"],
                    "MIN_ROUTES": str(lim["routes"]["min_routes_per_solution_fact"]),
                    "HERRING_MAX_TIER": str(lim["order"]["herring_induce_max_tier"]),
                    "MIN_DOCS_PER_SUSPECT": str(p["min_documents_per_suspect"]),
                    "MIN_AUTHORS_PER_SUSPECT": str(p["min_authors_per_suspect"]),
                    "WORLD_MIN": f"{int(w['world_clue_share_min'] * 100)} percent",
                    "WORLD_MAX": f"{int(w['world_clue_share_max'] * 100)} percent",
                    "AUTHORING_README": "`inputs/README_AUTHORING.md`",
                    "TURN_BUDGET": turn_budget("S2A")})
        outputs.append(("clue_plan.json", "the document plan"))

    elif stage == "S2B":
        put("bible.json", cp / "bible.json", desc="the sealed story and truth bible")
        put("clue_plan.json", cp / "clue_plan.json", desc="the accepted document plan")
        put("README_AUTHORING.md", _engine_path(root, eng["authoring_readme"]), desc="the authoring contract")
        put("fixture_case.json", _engine_path(root, eng["fixture_case"]), desc="a passing nonsense case: format example only")
        put("fixture_skin.json", _engine_path(root, eng["fixture_skin"]), desc="a passing nonsense skin: format example only")
        for rel in compat.get("engine_files", {}):
            put(f"engine_schemas/{Path(rel).name}", root / rel, desc="engine schema, vocabulary or contract")
        ctx.update({"AUTHORING_README": "`inputs/README_AUTHORING.md`", "TURN_BUDGET": turn_budget("S2B")})
        outputs += [("case.json", "the engine case with placeholders"), ("skin.json", "the engine skin")]

    elif stage in ("S3", "S4"):
        bible = K.load_json(cp / "bible.json")
        plan = K.load_json(cp / "clue_plan.json")
        owner = unit["owner"]
        phs = [ph for ph in plan["placeholders"] if ph["owner"] == owner]
        put("fill.schema.json", K.SCHEMA_DIR / "fill.schema.json", desc="the shape of your output")
        fact_ids = [f for ph in phs for f in ph["facts"]]
        ctx.update({"OWNER": owner, "WORLD_BRIEF": world_brief(bible), "CAST_NAMES": cast_names(bible),
                    "SLOTS_TABLE": slots_table(phs, bible), "FACTS_TABLE": facts_table(fact_ids, bible)})
        if stage == "S3":
            clue = next(c for c in plan["clues"] if c["id"] == owner)
            ctx.update(_s3_context(clue, plan, bible, phs))
            reg = cp / "media_registry.json"
            ctx["MEDIA_BRIEF"] = MD.brief_for(owner, plan, bible, K.load_json(reg) if reg.is_file() else None)
        else:
            ctx.update(_s4_context(bible, lim))
        outputs.append(("fill.json", "the texts and claims for the tokens in the table below"))

    elif stage == "S6":
        put("bible.json", cp / "bible.json", desc="the sealed bible")
        put("clue_plan.json", cp / "clue_plan.json", desc="the document plan")
        put("case.json", ws / cfg["workspace"]["case_file"], desc="the finished case")
        put("review.schema.json", K.SCHEMA_DIR / "review.schema.json", desc="the shape of your output")
        rub = [i for i in K.data("rubric")["items"] if i["tag"] == "SECOND-MODEL"]
        ctx["RUBRIC_TABLE"] = _bullets([f"{i['id']}: {i['text']}" for i in rub])
        ctx["FM_TABLE"] = _bullets([f"{m['id']} {m['name']}: {m['symptom']}" for m in K.data("failure_modes")["modes"]])
        outputs.append(("review.json", "scores and flags only"))

    ctx["INPUT_FILES"], ctx["OUTPUT_FILES"] = _io(inputs, outputs)
    ctx.setdefault("TURN_BUDGET", turn_budget(stage))
    tmpl = next(s for s in K.data("stage_plan")["stages"] if s["id"] == stage)["prompt"]
    text = render((K.PROMPTS_DIR / tmpl).read_text(encoding="utf-8"), ctx)
    text += inline_section(sdir, [rel for rel, _ in inputs])
    prompt = sdir / "prompt.md"
    prompt.write_text(text, encoding="utf-8", newline="\n")
    K.dump_json({"unit": unit["unit"], "stage": stage, "owner": unit.get("owner"),
                 "outputs": [o for o, _ in outputs]}, sdir / "unit.json")
    return prompt


def _s3_context(clue: dict, plan: dict, bible: dict, phs: list[dict]) -> dict[str, str]:
    forms = _by_id(K.data("document_forms")["forms"])
    techs = _by_id(K.data("document_forms")["techniques"])
    cast = _by_id(bible["cast"])
    form = forms.get(clue["form_id"], {"name": clue["form_id"], "purpose": "", "voice_tip": ""})
    form_lines = [f"Form {clue['form_id']}: {form['name']}, which exists for {form['purpose']}.",
                  f"How this kind of paper usually reads: {form['voice_tip']}."]
    for t in clue.get("technique_ids", []):
        if t in techs:
            form_lines.append(f"Technique {t} {techs[t]['name']}: {techs[t]['use']} Risk: {techs[t]['risk']}")
    author = clue["author"]
    if author in cast:
        a = cast[author]
        author_brief = (f"{a['name']['given']} {a['name']['family']} ({author}). "
                        f"What they notice: {a['attention']} How they write: {a['voice_notes']}")
        voice = f"Write as this person. {a['voice_notes']}"
        if a.get("voice_sample"):
            voice += ("\n\nHow this person writes when nothing is at stake (match the voice, never the content):\n> "
                      + a["voice_sample"])
    else:
        author_brief = f"department {author}"
        voice = "Findings are plain and measured in every department."
    profiles = _by_id(K.data("voice_matrix")["profiles"])
    if clue.get("dept"):
        dept = next((d for d in plan["departments"] if d["id"] == clue["dept"]), None)
        if dept and dept["voice_id"] in profiles:
            voice += "\n\nAssessment fields use this department voice:\n" + voice_profile_text(profiles[dept["voice_id"]])
    return {"FORM_BRIEF": "\n".join(form_lines), "AUTHOR_BRIEF": author_brief,
            "READER": clue["intended_reader"], "REASON": clue["in_world_reason"],
            "DATE": clue.get("date") or "as the form requires", "VOICE_BRIEF": voice,
            "REQUIRED_STRINGS": required_strings(phs, bible),
            "NEIGHBOURS": neighbours(clue["id"], plan, bible)}


def neighbours(owner: str, plan: dict, bible: dict) -> str:
    """A facts-free index of the other documents, so papers can refer to each other.

    It lists form, date and author only: no facts, roles, tiers or reasons.
    """
    forms = _by_id(K.data("document_forms")["forms"])
    cast = _by_id(bible["cast"])
    rows = []
    for c in sorted(plan["clues"], key=lambda x: (x.get("date") or "", x["id"])):
        if c["id"] == owner:
            continue
        form = forms.get(c["form_id"], {"name": c["form_id"]})["name"]
        who = c["author"]
        who = f"{cast[who]['name']['given']} {cast[who]['name']['family']}" if who in cast else f"department {who}"
        rows.append(f"{form}, dated {c.get('date') or 'undated'}, by {who}")
    return _bullets(rows)


def _s4_context(bible: dict, lim: dict) -> dict[str, str]:
    blocks = []
    for q in sorted(bible["questions"], key=lambda x: x["id"]):
        opts = sorted(q["options"], key=lambda o: o["id"])
        blocks.append(f"{q['id']}: {q['stem_gist']}\n" + _bullets([f"{o['id']}: {o['gist']}" for o in opts]))
    ents = [f"{c['name']['given']} {c['name']['family']}" for c in bible["cast"]] + [l["name"] for l in bible["locations"]]
    return {"QUESTIONS_TABLE": "\n\n".join(blocks), "ENTITY_LIST": _bullets(ents),
            "OPTION_TOLERANCE": f"{int(lim['prose']['option_length_tolerance'] * 100)} percent"}


def _prepare_repair(unit: dict, ws: Path, root: Path, state: dict, sdir: Path) -> Path:
    from repair_builder import failures_table
    target = unit["target"]
    tdir = Path(state["stage_root"]) / target
    if not (tdir / "unit.json").is_file():
        # the target was accepted and its folder closed; rebuild its original brief
        tstage = "S3" if target.startswith("S3-") else target  # S1, S2A, S2B, S4 or S6
        towner = target[3:] if target.startswith("S3-") else (K.data("stage_plan")["s4_owner"] if target == "S4" else None)
        prepare({"unit": target, "stage": tstage, "owner": towner}, ws, root, state)
    tinfo = K.load_json(tdir / "unit.json")
    inputs, outputs = [], []
    if (tdir / "inputs").is_dir():
        shutil.copytree(tdir / "inputs", sdir / "inputs", dirs_exist_ok=True)
        for p in sorted((tdir / "inputs").rglob("*")):
            if p.is_file():
                inputs.append((f"inputs/{p.relative_to(tdir / 'inputs').as_posix()}", "as in the original stage"))
    K.copy_file(tdir / "prompt.md", sdir / "inputs" / "original_brief.md")
    inputs.append(("inputs/original_brief.md", "the original stage brief"))
    prev_src = Path(state["failure"]["outputs_dir"])
    flagged = {f.get("file") for f in state["failure"]["findings"] if f.get("file")}
    for name in tinfo["outputs"]:
        src = prev_src / name
        if src.is_file():
            # Already in place under its output name, so an untouched file costs no turns.
            K.copy_file(src, sdir / name)
            note = "your previous output, already in place; it is broken, write it again whole" if name in flagged \
                else "your previous output, already in place; edit only if a failure needs it"
        else:
            note = "missing last time; write it"
        outputs.append((name, note))
    compat = K.load_json(ws / "checkpoints" / "compat.json")
    lim = K.data("limits")["repair"]
    ctx = {"HEADER": header(), "STAGE_ID": "S5", "TARGET_UNIT": target, "ROUND": str(unit["round"]),
           "MAX_ROUNDS": str(lim["max_repair_rounds"]),
           "FAILURES_TABLE": failures_table(state["failure"]["findings"], compat.get("rule_texts", {})),
           "TARGET_BRIEF_FILE": "inputs/original_brief.md",
           "TURN_BUDGET": turn_budget("S5", tinfo["stage"])}
    ctx["INPUT_FILES"], ctx["OUTPUT_FILES"] = _io(inputs, outputs)
    text = render((K.PROMPTS_DIR / K.data("stage_plan")["repair"]["prompt"]).read_text(encoding="utf-8"), ctx)
    # the original brief already carries its inputs in full; the previous outputs follow, so a fix needs no reads
    text += inline_section(sdir, ["inputs/original_brief.md"], "The original brief, in full")
    text += inline_section(sdir, [n for n in tinfo["outputs"] if (sdir / n).is_file()], "Your previous outputs, in full")
    prompt = sdir / "prompt.md"
    prompt.write_text(text, encoding="utf-8", newline="\n")
    K.dump_json({"unit": unit["unit"], "stage": "S5", "target": target, "target_stage": tinfo["stage"],
                 "owner": tinfo.get("owner"), "outputs": tinfo["outputs"]}, sdir / "unit.json")
    return prompt


# ---------------------------------------------------------------- blind audit (S7)

def prepare_audit(mode: str, ws: Path, bundle: dict, state: dict) -> Path:
    """Prepare one blind-audit unit. mode is SOLVE (full player bundle) or SHORTCUT (questions only)."""
    cfg = K.data("kit_config")
    unit_id = f"S7-{mode}"
    sdir = Path(state["stage_root"]) / unit_id
    _fresh_dir(sdir)
    if mode == "SOLVE":
        K.dump_json(bundle, sdir / "inputs" / "player_bundle.json")
        inputs = [("inputs/player_bundle.json", "the player-facing case, exactly as the player will see it")]
    else:
        K.dump_json(questions_only(bundle, cfg["audit"]), sdir / "inputs" / "questions_only.json")
        inputs = [("inputs/questions_only.json", "the questions and options only, with no records")]
    K.copy_file(K.SCHEMA_DIR / "answers.schema.json", sdir / "inputs" / "answers.schema.json")
    inputs.append(("inputs/answers.schema.json", "the shape of your output"))
    ctx = {"MODE": mode, "STAGE_ID": "S7"}
    ctx["INPUT_FILES"], ctx["OUTPUT_FILES"] = _io(inputs, [("answers.json", "your answers")])
    tmpl = K.data("stage_plan")["audit_prompts"][mode]
    text = render((K.PROMPTS_DIR / tmpl).read_text(encoding="utf-8"), ctx)
    prompt = sdir / "prompt.md"
    prompt.write_text(text, encoding="utf-8", newline="\n")
    K.dump_json({"unit": unit_id, "stage": "S7", "owner": None, "outputs": ["answers.json"]}, sdir / "unit.json")
    return prompt


def _get_path(obj, path: str):
    cur = obj
    for part in re.findall(r"\.([A-Za-z_][A-Za-z0-9_]*)|\[([0-9]+)\]", path):
        key, idx = part
        cur = cur[key] if key else cur[int(idx)]
    return cur


def questions_only(bundle: dict, acfg: dict) -> dict:
    """The questions and options from the bundle, with nothing else."""
    try:
        qs = _get_path(bundle, acfg["questions_path"])
    except (KeyError, IndexError, TypeError):
        raise K.KitError("ERR_BAD_BUNDLE", code=2)
    return {"questions": qs}
