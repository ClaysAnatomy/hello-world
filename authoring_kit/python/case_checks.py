"""case_checks: deterministic checks on the S1 bible and the S2 document plan.

Every finding is (check ID, JSON path or '$', severity). Nothing from the
bible or plan text is ever returned.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402

ERROR, WARN = "ERROR", "WARN"


def F(cid: str, path: str = "$", sev: str = ERROR) -> dict:
    return {"id": cid, "path": path, "sev": sev}


def has_errors(findings: list[dict]) -> bool:
    return any(f["sev"] == ERROR for f in findings)


def _ban_terms(cat_ids: set[str]) -> list[tuple[str, str, str]]:
    out = []
    for cat in K.data("ban_lists")["categories"]:
        if cat["id"] in cat_ids:
            for t in cat["terms"]:
                out.append((cat["check"], cat["severity"], t))
    return out


# ================================================================ bible

def check_bible(bible: dict, seeds: dict) -> list[dict]:
    lim = K.data("limits")
    out: list[dict] = []
    errs = K.schema_errors(bible, K.schema("bible"))
    if errs:
        return [F("KT-BI-01", p) for p in errs[:20]]

    id_rx = re.compile(lim["ids"]["opaque_id_regex"])
    all_ids: list[tuple[str, str]] = []
    for i, c in enumerate(bible["cast"]):
        all_ids.append((c["id"], f"$.cast[{i}].id"))
    for i, l in enumerate(bible["locations"]):
        all_ids.append((l["id"], f"$.locations[{i}].id"))
    for i, f in enumerate(bible["facts"]):
        all_ids.append((f["id"], f"$.facts[{i}].id"))
    for qi, q in enumerate(bible["questions"]):
        all_ids.append((q["id"], f"$.questions[{qi}].id"))
        for oi, o in enumerate(q["options"]):
            all_ids.append((o["id"], f"$.questions[{qi}].options[{oi}].id"))
    seen = set()
    for value, path in all_ids:
        if not id_rx.match(value) or value in seen:
            out.append(F("KT-BI-14", path))
        seen.add(value)

    # names
    seeded = {(n["given"], n["family"]) for n in seeds["cast_names"]}
    used = [(c["name"]["given"], c["name"]["family"]) for c in bible["cast"]]
    for i, nm in enumerate(used):
        if nm not in seeded:
            out.append(F("KT-BI-02", f"$.cast[{i}].name"))
    if len(set(used)) != len(used) or set(used) != seeded:
        out.append(F("KT-BI-02", "$.cast"))

    # budget
    b = lim["budget"]
    suspects = [c for c in bible["cast"] if c["role"] == "suspect"]
    if not (b["min_suspects"] <= len(suspects) <= b["max_suspects"]):
        out.append(F("KT-BI-03", "$.cast"))
    if len(bible["cast"]) > b["max_cast_total"]:
        out.append(F("KT-BI-03", "$.cast"))
    if len(bible["locations"]) > b["max_locations"]:
        out.append(F("KT-BI-03", "$.locations"))
    if len(bible["critical_strings"]) > b["max_critical_strings"]:
        out.append(F("KT-BI-03", "$.critical_strings"))

    # critical strings equal seeds
    seeded_cs = {c["id"]: c["value"] for c in seeds["critical_strings"]}
    got_cs = {c["id"]: c["value"] for c in bible["critical_strings"]}
    if got_cs != seeded_cs:
        out.append(F("KT-BI-13", "$.critical_strings"))

    facts = {f["id"]: f for f in bible["facts"]}
    cast = {c["id"]: c for c in bible["cast"]}
    for i, f in enumerate(bible["facts"]):
        for src in f.get("from", []):
            if src not in facts:
                out.append(F("KT-BI-04", f"$.facts[{i}].from"))

    # options
    options: dict[str, dict] = {}
    for qi, q in enumerate(bible["questions"]):
        correct = [o for o in q["options"] if o["correct"]]
        if len(correct) != 1:
            out.append(F("KT-BI-05", f"$.questions[{qi}].options"))
        for oi, o in enumerate(q["options"]):
            options[o["id"]] = o
            if len(set(o["support"])) < 2 or any(s not in facts for s in o["support"]):
                out.append(F("KT-BI-04", f"$.questions[{qi}].options[{oi}].support"))

    # culprit, method, motive
    t = bible["truth"]
    culprits = [c for c in bible["cast"] if c["is_culprit"]]
    if (len(culprits) != 1 or culprits[0]["id"] != t["culprit"] or culprits[0]["role"] != "suspect"):
        out.append(F("KT-BI-11", "$.truth.culprit"))
    for key in ("method_fact", "motive_fact"):
        f = facts.get(t[key])
        if not f or not f["solution_critical"]:
            out.append(F("KT-BI-11", f"$.truth.{key}"))

    # red herring
    rh = bible["red_herring"]
    target = options.get(rh["target_option"])
    sec = facts.get(rh["secondary_secret_fact"])
    sus = cast.get(rh["suspect"])
    if (target is None or target["correct"] or sec is None or sec["kind"] != "secondary"
            or sus is None or sus["role"] != "suspect" or sus["is_culprit"]
            or rh["type_id"] != seeds["red_herring"]
            or not rh["refuted_by_facts"] or any(x not in facts for x in rh["refuted_by_facts"])):
        out.append(F("KT-BI-06", "$.red_herring"))

    # aha
    if sorted(a["pattern_id"] for a in bible["aha"]) != sorted(seeds["patterns"]):
        out.append(F("KT-BI-07", "$.aha"))
    for ai, a in enumerate(bible["aha"]):
        trio = [a["mask_fact"], a["reframe_fact"], a["leads_to_fact"]]
        if len(set(trio)) != 3 or any(x not in facts for x in trio):
            out.append(F("KT-BI-07", f"$.aha[{ai}]"))

    # people
    min_rel = lim["people"]["min_relationships_per_person"]
    for i, c in enumerate(bible["cast"]):
        rels = [r for r in c["relationships"] if r["to"] in cast and r["to"] != c["id"]]
        if len({r["to"] for r in rels}) < min_rel:
            out.append(F("KT-BI-08", f"$.cast[{i}].relationships"))
        for key in ("want", "obligation", "attention", "pressure", "would_lie_about", "lie_reason", "life_outside", "voice_notes"):
            if not c[key].strip():
                out.append(F("KT-BI-08", f"$.cast[{i}].{key}"))

    # quirk and trope vocabulary
    quirk = _ban_terms({"BL-QUIRK"})
    for i, c in enumerate(bible["cast"]):
        blob = " ".join(str(c[k]) for k in ("want", "obligation", "attention", "pressure", "life_outside", "voice_notes")).lower()
        if any(K.phrase_in(blob, t) for _, _, t in quirk):
            out.append(F("KT-BI-09", f"$.cast[{i}]", WARN))
    trope = _ban_terms({"BL-TROPE"})
    blob = " ".join([bible["premise"]["hook"], bible["truth"]["what_happened"], bible["cover"]["official_story"]]).lower()
    if any(K.phrase_in(blob, t) for _, _, t in trope):
        out.append(F("KT-BI-10", "$.truth", WARN))

    # setting
    st = bible["premise"]["setting"]
    w = lim["world"]
    if len(st["texture"]) < w["min_setting_texture"]:
        out.append(F("KT-BI-12", "$.premise.setting.texture"))
    if len(st["internal_terms"]) < w["min_internal_terms"]:
        out.append(F("KT-BI-12", "$.premise.setting.internal_terms"))
    if len(st["rhythms"]) < w["min_rhythms"]:
        out.append(F("KT-BI-12", "$.premise.setting.rhythms"))
    return out


# ================================================================ plan

def check_plan(plan: dict, bible: dict, case_obj: dict, seeds: dict, s4_owner: str) -> list[dict]:
    lim = K.data("limits")
    forms = {f["id"] for f in K.data("document_forms")["forms"]}
    out: list[dict] = []
    errs = K.schema_errors(plan, K.schema("clue_plan"))
    if errs:
        return [F("KT-PL-01", p) for p in errs[:20]]

    facts = {f["id"]: f for f in bible["facts"]}
    cast = {c["id"]: c for c in bible["cast"]}
    suspects = [c["id"] for c in bible["cast"] if c["role"] == "suspect"]
    clues = {c["id"]: c for c in plan["clues"]}
    case_strings = set(K.string_leaves(case_obj))
    dept_ids = {d["id"] for d in plan["departments"]}

    # IDs
    if len(clues) != len(plan["clues"]):
        out.append(F("KT-PL-14", "$.clues"))
    for i, c in enumerate(plan["clues"]):
        if c["id"] not in case_strings:
            out.append(F("KT-PL-14", f"$.clues[{i}].id"))
        for fid in c["facts"]:
            if fid not in facts:
                out.append(F("KT-PL-15", f"$.clues[{i}].facts"))
        for m in c["mentions"]:
            if m not in cast:
                out.append(F("KT-PL-08", f"$.clues[{i}].mentions"))

    reused = [c["id"] for c in bible["cast"]] + [f["id"] for f in bible["facts"] if f["solution_critical"]]
    for q in bible["questions"]:
        reused.append(q["id"])
        reused.extend(o["id"] for o in q["options"])
    for rid in reused:
        if rid not in case_strings:
            out.append(F("KT-PL-12", "$"))
            break

    # routes
    r = lim["routes"]
    for fid, f in facts.items():
        if not f["solution_critical"]:
            continue
        routes = plan["routes"].get(fid, [])
        valid = []
        for route in routes:
            ids = route["clues"]
            if not ids or any(x not in clues for x in ids):
                continue
            covered = set().union(*[set(clues[x]["facts"]) for x in ids])
            if fid in covered or (f.get("from") and set(f["from"]) <= covered):
                valid.append(route)
        ok = len(valid) >= r["min_routes_per_solution_fact"]
        if ok and r["require_disjoint_pair"]:
            sets = [set(v["clues"]) for v in valid]
            ok = any(not (a & b) for i, a in enumerate(sets) for b in sets[i + 1:])
        if ok and r["require_search_free_route"]:
            ok = any(v["search_free"] and all(clues[x]["search_free"] for x in v["clues"]) for v in valid)
        if not ok:
            out.append(F("KT-PL-02", "$.routes"))

    # no single clue carries a correct option's whole support
    for q in bible["questions"]:
        for o in q["options"]:
            if o["correct"]:
                sup = set(o["support"])
                if any(sup <= set(c["facts"]) for c in plan["clues"]):
                    out.append(F("KT-PL-03", "$.clues"))

    # herring
    rh = bible["red_herring"]
    induce = [c for c in plan["clues"] if c["role"] == "herring_induce"]
    refute_tiers = [c["tier"] for c in plan["clues"] if set(c["facts"]) & set(rh["refuted_by_facts"])]
    secret_held = any(rh["secondary_secret_fact"] in c["facts"] for c in plan["clues"])
    if (not induce or min(c["tier"] for c in induce) > lim["order"]["herring_induce_max_tier"]
            or not refute_tiers or not secret_held
            or min(refute_tiers) <= min(c["tier"] for c in induce)):
        out.append(F("KT-PL-04", "$.clues"))

    # aha
    for a in bible["aha"]:
        mask_t = [c["tier"] for c in plan["clues"] if a["mask_fact"] in c["facts"]]
        ref_t = [c["tier"] for c in plan["clues"] if a["reframe_fact"] in c["facts"]]
        stated = any(a["leads_to_fact"] in c["facts"] for c in plan["clues"])
        if not mask_t or not ref_t or min(mask_t) >= min(ref_t) or stated:
            out.append(F("KT-PL-05", "$.clues"))

    # people on paper
    p = lim["people"]
    crit = {fid for fid, f in facts.items() if f["solution_critical"]}
    for sid in suspects:
        docs = [c for c in plan["clues"] if sid in c["mentions"] or c["author"] == sid]
        authors = {c["author"] for c in docs}
        non_crime = [c for c in docs if not (set(c["facts"]) & crit)]
        if (len(docs) < p["min_documents_per_suspect"] or len(authors) < p["min_authors_per_suspect"]
                or (p["require_non_crime_appearance"] and not non_crime)):
            out.append(F("KT-PL-06", "$.clues"))

    # forms
    w = lim["world"]
    counts: dict[str, int] = {}
    for i, c in enumerate(plan["clues"]):
        if c["form_id"] not in forms:
            out.append(F("KT-PL-07", f"$.clues[{i}].form_id"))
        counts[c["form_id"]] = counts.get(c["form_id"], 0) + 1
    n = len(plan["clues"])
    if len(counts) < min(w["min_distinct_forms"], n) or max(counts.values()) / n > w["max_form_share"] + 1e-9:
        out.append(F("KT-PL-07", "$.clues"))

    # authorship
    for i, c in enumerate(plan["clues"]):
        if c["author"] not in cast and c["author"] not in dept_ids:
            out.append(F("KT-PL-08", f"$.clues[{i}].author"))
        if not c["intended_reader"].strip() or not c["in_world_reason"].strip():
            out.append(F("KT-PL-08", f"$.clues[{i}]"))
        if c.get("dept") and c["dept"] not in dept_ids:
            out.append(F("KT-PL-09", f"$.clues[{i}].dept"))

    # departments and voices
    voices = [d["voice_id"] for d in plan["departments"]]
    if (len(voices) != len(set(voices)) or any(v not in seeds["dept_mix"] for v in voices)
            or len(voices) > lim["budget"]["max_departments"]):
        out.append(F("KT-PL-09", "$.departments"))

    # world share
    world = [c for c in plan["clues"] if c["role"] == "world"]
    share = len(world) / n
    if share < w["world_clue_share_min"] - 1e-9 or share > w["world_clue_share_max"] + 1e-9:
        out.append(F("KT-PL-11", "$.clues"))
    for c in world:
        if not c["mentions"] and c["author"] not in cast:
            out.append(F("KT-PL-11", "$.clues"))
            break

    # placeholders
    rx = K.placeholder_regex(lim["ids"]["placeholder_format"])
    find_rx = K.placeholder_search_regex(lim["ids"]["placeholder_format"])
    listed = {}
    for i, ph in enumerate(plan["placeholders"]):
        m = rx.match(ph["token"])
        bad = (m is None or m.group("owner") != ph["owner"] or ph["token"] in listed)
        if ph["stage"] == "S3":
            bad = bad or ph["owner"] not in clues or not set(ph["facts"]) <= set(clues[ph["owner"]]["facts"])
        else:
            bad = bad or ph["owner"] != s4_owner or any(x not in facts for x in ph["facts"])
        if any(cs not in {c["id"] for c in bible["critical_strings"]} for cs in ph["required_strings"]):
            bad = True
        if bad:
            out.append(F("KT-PL-10", f"$.placeholders[{i}]"))
        listed[ph["token"]] = ph
    occurrences = K.token_paths(case_obj, rx)
    for tok in listed:
        if len(occurrences.get(tok, [])) != 1:
            out.append(F("KT-PL-10", "$.placeholders"))
            break
    for parts, value in K.walk_leaves(case_obj):
        if isinstance(value, str) and find_rx.search(value) and value not in listed:
            out.append(F("KT-PL-10", K.jpath(parts)))

    # every critical string is required somewhere
    required = {cs for ph in plan["placeholders"] for cs in ph["required_strings"]}
    for cs in bible["critical_strings"]:
        if cs["id"] not in required:
            out.append(F("KT-PL-13", "$.placeholders"))
    return out


def s3_owners(plan: dict) -> list[str]:
    """Document owners in reading order: tier, then ID."""
    owners = {ph["owner"] for ph in plan["placeholders"] if ph["stage"] == "S3"}
    tiers = {c["id"]: c["tier"] for c in plan["clues"]}
    return sorted(owners, key=lambda o: (tiers.get(o, 99), o))
