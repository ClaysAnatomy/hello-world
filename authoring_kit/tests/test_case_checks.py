"""Tests for case_checks: the bible (S1) and the document plan (S2). Run: python test_case_checks.py"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_test_util import FIXTURE_ROOT, K, Report, override_data, reset_data  # noqa: E402
import scenario  # noqa: E402
import case_checks as CC  # noqa: E402
from compat_check import run_compat  # noqa: E402
from seed_sampler import sample  # noqa: E402

r = Report("test_case_checks")
reset_data()
seeds = sample(7, run_compat(FIXTURE_ROOT))
bible = scenario.make_bible(seeds)
plan, case, skin = scenario.make_s2(bible, seeds)


def ids(findings, sev=None):
    return sorted({f["id"] for f in findings if sev is None or f["sev"] == sev})


r.eq("clean bible", CC.check_bible(bible, seeds), [])
r.eq("clean plan", CC.check_plan(plan, bible, case, seeds, "DESK-01"), [])


def bible_mut(fn):
    b = copy.deepcopy(bible)
    fn(b)
    return ids(CC.check_bible(b, seeds), "ERROR")


r.eq("schema", bible_mut(lambda b: b.pop("cover")), ["KT-BI-01"])
r.eq("name not seeded", bible_mut(lambda b: b["cast"][0]["name"].update({"given": "Elias"})), ["KT-BI-02"])
r.eq("too many locations", bible_mut(lambda b: b["locations"].extend([{"id": f"LOC-{i}", "name": f"L{i}", "note": "x"} for i in range(3, 6)])), ["KT-BI-03"])
r.eq("one supporting fact", bible_mut(lambda b: b["questions"][0]["options"][0].update({"support": ["FACT-01"]})), ["KT-BI-04"])
r.eq("two correct", bible_mut(lambda b: b["questions"][0]["options"][1].update({"correct": True})), ["KT-BI-05", "KT-BI-06"])
r.eq("herring on culprit", bible_mut(lambda b: b["red_herring"].update({"suspect": "CHAR-S1"})), ["KT-BI-06"])
r.eq("herring secret wrong kind", bible_mut(lambda b: b["red_herring"].update({"secondary_secret_fact": "FACT-01"})), ["KT-BI-06"])
r.eq("aha wrong pattern", bible_mut(lambda b: b["aha"][0].update({"pattern_id": "PAT-01"})), ["KT-BI-07"])
r.eq("aha same fact twice", bible_mut(lambda b: b["aha"][0].update({"reframe_fact": "FACT-07"})), ["KT-BI-07"])
r.eq("missing relationships", bible_mut(lambda b: b["cast"][0].update({"relationships": []})), ["KT-BI-08"])
r.eq("blank sheet field", bible_mut(lambda b: b["cast"][1].update({"want": "  "})), ["KT-BI-08"])
r.eq("motive not critical", bible_mut(lambda b: b["facts"][1].update({"solution_critical": False})), ["KT-BI-11"])
r.eq("setting thin", bible_mut(lambda b: b["premise"]["setting"].update({"texture": ["a"]})), ["KT-BI-12"])
r.eq("critical string changed", bible_mut(lambda b: b["critical_strings"][0].update({"value": "12:30"})), ["KT-BI-13"])
r.eq("bad ID", bible_mut(lambda b: b["locations"][0].update({"id": "the boathouse"})), ["KT-BI-14"])

b = copy.deepcopy(bible)
b["cast"][0]["attention"] = "an eccentric with a trademark scarf"
b["truth"]["what_happened"] = "the evil twin did it"
r.eq("quirk and trope warn", ids(CC.check_bible(b, seeds), "WARN"), ["KT-BI-09", "KT-BI-10"])
r.eq("warnings do not fail", ids(CC.check_bible(b, seeds), "ERROR"), [])


def plan_mut(fn, case_fn=None):
    p = copy.deepcopy(plan)
    c = copy.deepcopy(case)
    fn(p)
    if case_fn:
        case_fn(c)
    return ids(CC.check_plan(p, bible, c, seeds, "DESK-01"), "ERROR")


def clue(p, cid):
    return next(c for c in p["clues"] if c["id"] == cid)


r.eq("plan schema", plan_mut(lambda p: p.pop("routes")), ["KT-PL-01"])
r.eq("one route only", plan_mut(lambda p: p["routes"]["FACT-01"].pop()), ["KT-PL-02"])
r.eq("routes overlap", plan_mut(lambda p: p["routes"]["FACT-03"].__setitem__(1, {"clues": ["CLUE-02", "CLUE-08"], "search_free": True})), ["KT-PL-02"])
r.eq("no search-free route", plan_mut(lambda p: [c.update({"search_free": False}) for c in p["clues"]]), ["KT-PL-02"])
r.eq("one clue holds the answer", plan_mut(lambda p: clue(p, "CLUE-04")["facts"].append("FACT-03")), ["KT-PL-03"])
r.eq("herring induced late", plan_mut(lambda p: clue(p, "CLUE-01").update({"tier": 2})), ["KT-PL-04"])
r.eq("reframe before mask", plan_mut(lambda p: [clue(p, x).update({"tier": 0}) for x in ("CLUE-07", "CLUE-09")] and None
                                     or [clue(p, x).update({"tier": 1}) for x in ("CLUE-02",)]), ["KT-PL-05"])
r.eq("aha conclusion stated", plan_mut(lambda p: clue(p, "CLUE-07")["facts"].append("FACT-09")), ["KT-PL-03", "KT-PL-05"])
r.eq("suspect missing from paper", plan_mut(lambda p: [c.update({"mentions": [m for m in c["mentions"] if m != "CHAR-S3"]}) for c in p["clues"]]
                                            or clue(p, "CLUE-03").update({"author": "CHAR-V1"})), ["KT-PL-06"])
r.eq("unknown form", plan_mut(lambda p: clue(p, "CLUE-05").update({"form_id": "DF-99"})), ["KT-PL-07"])
r.eq("one form dominates", plan_mut(lambda p: [c.update({"form_id": "DF-01"}) for c in p["clues"][:5]]), ["KT-PL-07"])
r.eq("no in-world reason", plan_mut(lambda p: clue(p, "CLUE-05").update({"in_world_reason": " "})), ["KT-PL-08"])
r.eq("unknown author", plan_mut(lambda p: clue(p, "CLUE-05").update({"author": "CHAR-X9"})), ["KT-PL-08"])
r.eq("voices repeat", plan_mut(lambda p: p["departments"][1].update({"voice_id": p["departments"][0]["voice_id"]})), ["KT-PL-09"])
r.eq("too much world", plan_mut(lambda p: [c.update({"role": "world"}) for c in p["clues"][3:8]]), ["KT-PL-11"])
r.eq("placeholder missing in case", plan_mut(lambda p: None, lambda c: c["clues"][0].update({"record_title": "Typed title"})), ["KT-PL-10"])
r.eq("stray placeholder in case", plan_mut(lambda p: None, lambda c: c["clues"][0].update({"overlay_text": "PP-CLUE-01-9"})), ["KT-PL-10"])
r.eq("placeholder claims foreign fact", plan_mut(lambda p: p["placeholders"][1]["facts"].append("FACT-02")), ["KT-PL-10"])
r.eq("bible IDs not reused", plan_mut(lambda p: None, lambda c: c["characters"].pop(0)), ["KT-PL-12"])
r.eq("critical string unassigned", plan_mut(lambda p: [ph.update({"required_strings": []}) for ph in p["placeholders"]]), ["KT-PL-13"])
r.eq("clue not in case", plan_mut(lambda p: None, lambda c: c["clues"][4].update({"clue_id": "CLUE-55"})), ["KT-PL-14"])
r.eq("unknown fact", plan_mut(lambda p: clue(p, "CLUE-05")["facts"].append("FACT-77")), ["KT-PL-15"])

# names: rule-passing replacements are allowed; broken ones are not
def names_mut(pairs):
    b = copy.deepcopy(bible)
    for i, (g, f) in pairs.items():
        b["cast"][i]["name"] = {"given": g, "family": f}
    return ids(CC.check_bible(b, seeds), "ERROR")


r.eq("replacement name passing the rules", names_mut({0: ("Yusuf", "Zeller")}), [])
r.eq("replacement name that is banned", names_mut({0: ("Elias", "Zeller")}), ["KT-BI-02"])
r.eq("replacement repeating an initial", names_mut({0: (bible["cast"][1]["name"]["given"][0] + "lfred", "Zeller")}), ["KT-BI-02"])
r.eq("replacement not ASCII", names_mut({0: ("Zo\u00eb", "Zeller")}), ["KT-BI-02"])
r.eq("cast size must match seeds", bible_mut(lambda b: b["cast"].pop()), ["KT-BI-02", "KT-BI-08"])

r.eq("voice sample too short", bible_mut(lambda b: b["cast"][0].update({"voice_sample": "Too short."})), ["KT-BI-15"])
r.eq("voice sample with signposting", bible_mut(lambda b: b["cast"][0].update({"voice_sample": b["cast"][0]["voice_sample"] + " A chill ran down the hall."})), ["KT-BI-15"])

r.eq("world document carries a critical fact", plan_mut(lambda p: clue(p, "CLUE-03")["facts"].append("FACT-01")
                                                       or p["routes"]["FACT-01"].append({"clues": ["CLUE-03"], "search_free": True})), ["KT-PL-11"])
r.eq("world document over the flavor cap", plan_mut(lambda p: [ph.update({"max_words": 400}) for ph in p["placeholders"] if ph["owner"] == "CLUE-03"]), ["KT-PL-11"])
r.eq("too few tiers", plan_mut(lambda p: [c.update({"tier": min(c["tier"], 1)}) for c in p["clues"]]), ["KT-PL-17"])
lim = copy.deepcopy(K.data("limits"))
lim["world"]["max_documents"] = 8
override_data("limits", lim)
r.eq("too many documents for this build", plan_mut(lambda p: None), ["KT-PL-16"])
reset_data()

r.eq("s3 owner order", CC.s3_owners(plan),
     ["CLUE-01", "CLUE-02", "CLUE-03", "CLUE-04", "CLUE-05", "CLUE-08", "CLUE-10", "CLUE-06", "CLUE-07", "CLUE-09"])

sys.exit(r.finish())
