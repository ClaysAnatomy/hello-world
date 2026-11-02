"""Builds a complete NONSENSE case for any seeds, shaped to pass every kit check.

Used by the tests to stand in for a model. All prose is FIXTURE text plus two
canaries: CANARY (in prose) and KEY_CANARY (only in the sealed answer key).
"""
from __future__ import annotations

import json
from pathlib import Path

CANARY = "marmalade lighthouse quorum"
KEY_CANARY = "zebra answerkey"


def _person(i, cid, role, name, culprit, ids):
    nxt, prv = ids[(i + 1) % len(ids)], ids[(i - 1) % len(ids)]
    return {
        "id": cid, "name": {"given": name["given"], "family": name["family"]}, "role": role, "is_culprit": culprit,
        "want": f"FIXTURE want {i:02d}", "obligation": f"FIXTURE obligation {i:02d}",
        "attention": f"FIXTURE attention {i:02d}", "pressure": f"FIXTURE pressure {i:02d}",
        "would_lie_about": f"FIXTURE lie {i:02d}", "lie_reason": f"FIXTURE reason {i:02d}",
        "life_outside": f"FIXTURE life {i:02d}", "voice_notes": f"FIXTURE voice {i:02d}", "secret": None,
        "voice_sample": " ".join(["FIXTURE sample sentence", f"{i:02d}", "about stores and shifts."] * 8),
        "relationships": [{"to": nxt, "nature": f"FIXTURE tie {i:02d}a"}, {"to": prv, "nature": f"FIXTURE tie {i:02d}b"}],
    }


def make_bible(seeds: dict) -> dict:
    n_s = seeds["suspect_count"]
    names = seeds["cast_names"]
    ids = [f"CHAR-S{i + 1}" for i in range(n_s)] + ["CHAR-V1"] + [f"CHAR-W{i + 1}" for i in range(len(names) - n_s - 1)]
    roles = ["suspect"] * n_s + ["subject"] + ["witness"] * (len(names) - n_s - 1)
    cast = [_person(i, ids[i], roles[i], names[i], ids[i] == "CHAR-S1", ids) for i in range(len(names))]
    facts = [
        ("FACT-01", "base", True), ("FACT-02", "base", True), ("FACT-03", "base", True),
        ("FACT-04", "secondary", False), ("FACT-05", "herring", False), ("FACT-06", "base", False),
        ("FACT-07", "base", False), ("FACT-08", "base", False), ("FACT-09", "derived", True),
        ("FACT-10", "world", False), ("FACT-11", "base", False), ("FACT-12", "base", False),
        ("FACT-13", "derived", False),
    ]
    fact_objs = []
    for fid, kind, crit in facts:
        f = {"id": fid, "statement": f"FIXTURE statement {fid} {CANARY}", "kind": kind, "solution_critical": crit}
        if fid == "FACT-09":
            f["from"] = ["FACT-07", "FACT-08"]
        if fid == "FACT-13":
            f["from"] = ["FACT-11", "FACT-12"]
        fact_objs.append(f)
    aha = [{"pattern_id": seeds["patterns"][0], "mask_fact": "FACT-07", "reframe_fact": "FACT-08",
            "leads_to_fact": "FACT-09", "how_it_reframes": "FIXTURE reframe 01"}]
    if len(seeds["patterns"]) > 1:
        aha.append({"pattern_id": seeds["patterns"][1], "mask_fact": "FACT-11", "reframe_fact": "FACT-12",
                    "leads_to_fact": "FACT-13", "how_it_reframes": "FIXTURE reframe 02"})
    return {
        "kit_version": "1.0.0",
        "premise": {
            "hook": f"FIXTURE hook {KEY_CANARY}", "human_question": "FIXTURE question 01",
            "central_irony": "FIXTURE irony 01", "stakes_id": seeds["stakes"], "ending_note": f"FIXTURE ending {KEY_CANARY}",
            "anchors_honoured": [],
            "setting": {"place": "FIXTURE place 01", "institution": "FIXTURE institution 01", "era": "FIXTURE era 01",
                        "before_problem": "FIXTURE problem 01",
                        "texture": [f"FIXTURE texture {i:02d}" for i in range(1, 6)],
                        "internal_terms": [{"term": f"FX{i}", "meaning": f"FIXTURE meaning {i:02d}"} for i in range(1, 4)],
                        "rhythms": ["FIXTURE rhythm 01", "FIXTURE rhythm 02"]},
        },
        "cast": cast,
        "locations": [{"id": "LOC-1", "name": "Wardhouse", "note": "FIXTURE note 01"},
                      {"id": "LOC-2", "name": "Pumproom", "note": "FIXTURE note 02"}],
        "critical_strings": [{"id": c["id"], "value": c["value"], "meaning": f"FIXTURE meaning {c['id']}"} for c in seeds["critical_strings"]],
        "facts": fact_objs,
        "questions": [
            {"id": "Q01", "stem_gist": "FIXTURE who", "options": [
                {"id": "OPT-Q01-A", "gist": "FIXTURE gist A", "correct": True, "support": ["FACT-01", "FACT-03"], "entity": "CHAR-S1"},
                {"id": "OPT-Q01-B", "gist": "FIXTURE gist B", "correct": False, "support": ["FACT-05", "FACT-04"], "entity": "CHAR-S2"},
                {"id": "OPT-Q01-C", "gist": "FIXTURE gist C", "correct": False, "support": ["FACT-06", "FACT-03"], "entity": "CHAR-S3"}]},
            {"id": "Q02", "stem_gist": "FIXTURE why", "options": [
                {"id": "OPT-Q02-A", "gist": "FIXTURE gist D", "correct": True, "support": ["FACT-02", "FACT-09"]},
                {"id": "OPT-Q02-B", "gist": "FIXTURE gist E", "correct": False, "support": ["FACT-04", "FACT-10"]}]},
        ],
        "truth": {"what_happened": f"FIXTURE truth {KEY_CANARY}", "timeline": [{"at": seeds["critical_strings"][0]["value"], "event": "FIXTURE event 01", "fact": "FACT-03"}],
                  "culprit": "CHAR-S1", "method_fact": "FACT-01", "motive_fact": "FACT-02", "why_it_matters": f"FIXTURE why {KEY_CANARY}"},
        "cover": {"official_story": "FIXTURE cover 01", "maintained_by": ["CHAR-S1"]},
        "red_herring": {"type_id": seeds["red_herring"], "target_option": "OPT-Q01-B", "suspect": "CHAR-S2",
                        "secondary_secret_fact": "FACT-04", "why_it_misleads": "FIXTURE misleads 01", "refuted_by_facts": ["FACT-06"]},
        "aha": aha,
        "mechanism_id": seeds["mechanism"],
    }


# two documents reach the player as artifacts: a stamped report form and a handwritten note
MEDIA = {
    "CLUE-01": {"kind": "MF-05", "regions": {"body": "PP-CLUE-01-2"}, "handling": 2, "storage": "filed"},
    "CLUE-07": {"kind": "MF-06", "regions": {"body": "PP-CLUE-07-2"}, "handling": 3, "storage": "pocket"},
}

CLUES = [
    # id, tier, form, author key, role, facts, dept
    ("CLUE-01", 0, "DF-01", "DEPT-D1", "herring_induce", ["FACT-05"], "DEPT-D1"),
    ("CLUE-02", 0, "DF-02", "CHAR-W1", "mask", ["FACT-07", "FACT-03", "FACT-11"], None),
    ("CLUE-03", 0, "DF-12", "CHAR-S3", "world", ["FACT-10"], None),
    ("CLUE-04", 1, "DF-14", "DEPT-D2", "solution", ["FACT-01"], "DEPT-D2"),
    ("CLUE-05", 1, "DF-03", "CHAR-S2", "support", ["FACT-04"], None),
    ("CLUE-06", 2, "DF-09", "DEPT-D1", "herring_refute", ["FACT-06", "FACT-12"], "DEPT-D1"),
    ("CLUE-07", 2, "DF-06", "CHAR-V1", "reframe", ["FACT-08", "FACT-02"], None),
    ("CLUE-08", 1, "DF-10", "CHAR-W1", "mask", ["FACT-07", "FACT-03"], None),
    ("CLUE-09", 2, "DF-08", "DEPT-D2", "reframe", ["FACT-08", "FACT-01", "FACT-02"], "DEPT-D2"),
    ("CLUE-10", 1, "DF-16", "CHAR-S1", "world", ["FACT-10"], None),
]


def make_s2(bible: dict, seeds: dict) -> tuple[dict, dict, dict]:
    suspects = [c["id"] for c in bible["cast"] if c["role"] == "suspect"]
    witness = next((c["id"] for c in bible["cast"] if c["role"] == "witness"), "CHAR-V1")
    clues, placeholders, case_clues = [], [], []
    cs_ids = [c["id"] for c in bible["critical_strings"]]
    for cid, tier, form, author, role, facts, dept in CLUES:
        author = witness if author == "CHAR-W1" else author
        mentions = suspects if role == "world" else [suspects[0]]
        clues.append({"id": cid, "form_id": form, "author": author, "intended_reader": "FIXTURE reader",
                      "in_world_reason": "FIXTURE reason", "date": "2026-03-04", "tier": tier, "facts": list(facts),
                      "mentions": mentions, "dept": dept, "search_free": True, "role": role})
        if cid == "CLUE-03":
            clues[-1]["purpose"] = {"kind": "teaches_rule", "term": "FX1", "note": "FIXTURE purpose 01"}
        if cid == "CLUE-10":
            clues[-1]["purpose"] = {"kind": "character_dynamic", "people": suspects[:2], "note": "FIXTURE purpose 02"}
        if cid in MEDIA:
            clues[-1]["media"] = json.loads(json.dumps(MEDIA[cid]))
        n = 1
        rec = {"clue_id": cid, "record_date": "2026-03-04", "relations": [{"type": "ESTABLISHES", "fact_id": f} for f in facts]}
        tok = f"PP-{cid}-{n}"
        rec["record_title"] = tok
        placeholders.append({"token": tok, "owner": cid, "stage": "S3", "slot": "record title", "kind": "title",
                             "facts": [], "required_strings": [], "max_words": 12})
        n += 1
        tok = f"PP-{cid}-{n}"
        rec["raw_observation_text"] = tok
        req = []
        if cid == "CLUE-02":
            req = [cs_ids[0]]
        if cid == "CLUE-08" and len(cs_ids) > 1:
            req = [cs_ids[1]]
        placeholders.append({"token": tok, "owner": cid, "stage": "S3", "slot": "raw observation",
                             "kind": "finding" if dept else "body", "facts": list(facts), "required_strings": req, "max_words": 120})
        if dept:
            n += 1
            tok = f"PP-{cid}-{n}"
            rec["dept_commentary_text"] = tok
            rec["is_dept_processed"] = True
            placeholders.append({"token": tok, "owner": cid, "stage": "S3", "slot": "department commentary",
                                 "kind": "assessment", "facts": [], "required_strings": [], "max_words": 120})
        case_clues.append(rec)
    questions, k = [], 1
    for q in bible["questions"]:
        stem = f"PP-DESK-01-{k}"
        placeholders.append({"token": stem, "owner": "DESK-01", "stage": "S4", "slot": "question stem", "kind": "stem",
                             "facts": [], "required_strings": [], "max_words": 30, "question": q["id"], "option": None})
        k += 1
        opts = []
        for o in q["options"]:
            tok = f"PP-DESK-01-{k}"
            k += 1
            placeholders.append({"token": tok, "owner": "DESK-01", "stage": "S4", "slot": "option text", "kind": "option",
                                 "facts": [], "required_strings": [], "max_words": 30, "question": q["id"], "option": o["id"]})
            opts.append({"option_id": o["id"], "text": tok})
        questions.append({"question_id": q["id"], "prompt_stem": stem, "options": opts})
    routes = {
        "FACT-01": [{"clues": ["CLUE-04"], "search_free": True}, {"clues": ["CLUE-09"], "search_free": True}],
        "FACT-02": [{"clues": ["CLUE-07"], "search_free": True}, {"clues": ["CLUE-09"], "search_free": True}],
        "FACT-03": [{"clues": ["CLUE-02"], "search_free": True}, {"clues": ["CLUE-08"], "search_free": True}],
        "FACT-09": [{"clues": ["CLUE-02", "CLUE-07"], "search_free": True}, {"clues": ["CLUE-08", "CLUE-09"], "search_free": True}],
    }
    plan = {"clues": clues, "routes": routes, "media_environment": {"climate": "polar", "hemisphere": "north"},
            "departments": [{"id": "DEPT-D1", "voice_id": seeds["dept_mix"][0]}, {"id": "DEPT-D2", "voice_id": seeds["dept_mix"][1]}],
            "placeholders": placeholders}
    case = {"case_id": "CASE-T-01",
            "characters": [{"char_id": c["id"], "display_name": f"{c['name']['given']} {c['name']['family']}"} for c in bible["cast"]],
            "locations": [{"location_id": l["id"], "name": l["name"]} for l in bible["locations"]],
            "facts": [{"fact_id": f["id"]} for f in bible["facts"]],
            "clues": case_clues, "questions": questions}
    skin = {"skin_id": "SKIN-T-01", "departments": [{"dept_id": "DEPT-D1", "label": "FIXTURE dept 1"}, {"dept_id": "DEPT-D2", "label": "FIXTURE dept 2"}]}
    return plan, case, skin


def _voice_text(plan: dict, owner: str) -> str:
    sys_path = Path(__file__).resolve().parents[2] / "data" / "voice_matrix.json"
    profiles = {p["id"]: p for p in json.loads(sys_path.read_text(encoding="utf-8"))["profiles"]}
    clue = next(c for c in plan["clues"] if c["id"] == owner)
    voice = next(d["voice_id"] for d in plan["departments"] if d["id"] == clue["dept"])
    same_dept = [c["id"] for c in plan["clues"] if c.get("dept") == clue["dept"]]
    return profiles[voice]["exemplars"][same_dept.index(owner) % len(profiles[voice]["exemplars"])]


def media_values(owner: str, plan: dict, bible: dict, seeds: dict | None) -> str:
    """The registry values a media document must print, as the fake writer would copy them."""
    if not seeds or not any(c.get("media") for c in plan["clues"]):
        return ""
    import media as MD
    reg = MD.build_registry(plan, bible, seeds)
    return " ".join(v for _, v in sorted(MD.required_values(owner, reg).items()))


def make_fill(owner: str, plan: dict, bible: dict, override: dict | None = None, seeds: dict | None = None) -> dict:
    crit = {c["id"]: c["value"] for c in bible["critical_strings"]}
    printed = media_values(owner, plan, bible, seeds)
    fills, claims = {}, {}
    num = owner.split("-")[-1]
    for ph in plan["placeholders"]:
        if ph["owner"] != owner:
            continue
        tok = ph["token"]
        if ph["kind"] == "title":
            text = f"Form record {num}"
        elif ph["kind"] == "assessment":
            text = _voice_text(plan, owner)
        elif ph["kind"] in ("finding", "body"):
            req = " ".join(crit[c] for c in ph["required_strings"])
            text = f"FIXTURE text {num} for record {owner} item noted {req} {CANARY}.".replace("  ", " ")
            if printed and ph["kind"] in ("finding", "body"):
                text = f"{printed}. {text}"
        elif ph["kind"] == "stem":
            text = f"FIXTURE stem for {ph['question']}"
        else:
            text = None
        fills[tok] = text
        if ph["facts"]:
            claims[tok] = list(ph["facts"])
    # options: equal length, each names a real person
    cast = {c["id"]: c for c in bible["cast"]}
    opts = [ph for ph in plan["placeholders"] if ph["owner"] == owner and ph["kind"] == "option"]
    if opts:
        options = {o["id"]: o for q in bible["questions"] for o in q["options"]}
        raw = {}
        for ph in opts:
            o = options[ph["option"]]
            ent = cast.get(o.get("entity") or "CHAR-S1")
            raw[ph["token"]] = f"Option naming {ent['name']['family']}"
        width = max(len(t) for t in raw.values())
        for tok, t in raw.items():
            fills[tok] = t + "." * (width - len(t))
    for tok, text in (override or {}).items():
        fills[tok] = text
    return {"owner": owner, "fills": fills, "claims": claims}


def write_outputs(agent_dir: Path, unit: str, files: dict[str, dict]) -> None:
    d = agent_dir / unit
    d.mkdir(parents=True, exist_ok=True)
    for name, obj in files.items():
        (d / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def stage_all(agent_dir: Path, seeds: dict, overrides: dict | None = None) -> tuple[dict, dict, dict, dict]:
    """Write canned outputs for S1, S2, every S3 owner and S4. Returns bible, plan, case, skin."""
    overrides = overrides or {}
    bible = make_bible(seeds)
    plan, case, skin = make_s2(bible, seeds)
    write_outputs(agent_dir, "S1", {"bible.json": bible})
    write_outputs(agent_dir, "S2", {"clue_plan.json": plan, "case.json": case, "skin.json": skin})
    owners = sorted({ph["owner"] for ph in plan["placeholders"] if ph["stage"] == "S3"})
    for o in owners:
        write_outputs(agent_dir, f"S3-{o}", {"fill.json": make_fill(o, plan, bible, overrides.get(o), seeds)})
    write_outputs(agent_dir, "S4", {"fill.json": make_fill("DESK-01", plan, bible, overrides.get("DESK-01"))})
    return bible, plan, case, skin
