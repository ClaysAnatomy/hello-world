"""Tests for voice_lint: prose checks on fills. Run: python test_voice_lint.py"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_test_util import FIXTURE_ROOT, K, Report, reset_data  # noqa: E402
import scenario  # noqa: E402
import voice_lint as VL  # noqa: E402
from compat_check import run_compat  # noqa: E402
from seed_sampler import sample  # noqa: E402

r = Report("test_voice_lint")
reset_data()
seeds = sample(7, run_compat(FIXTURE_ROOT))
bible = scenario.make_bible(seeds)
plan, case, skin = scenario.make_s2(bible, seeds)


def lint(owner, override=None, mutate=None):
    fill = scenario.make_fill(owner, plan, bible, override)
    if mutate:
        mutate(fill)
    return sorted({(f["id"], f["path"], f["sev"]) for f in VL.lint_fill(fill, owner, plan, bible)})


owners = sorted({ph["owner"] for ph in plan["placeholders"]})
for o in owners:
    r.eq(f"clean fill {o}", lint(o), [])

# every voice exemplar passes its own profile's rules
for p in K.data("voice_matrix")["profiles"]:
    for i, ex in enumerate(p["exemplars"]):
        r.eq(f"exemplar {p['id']} {i}", VL._voice_rules(ex, "X", p), [])

T = "PP-CLUE-04-2"   # finding of a department document
A = "PP-CLUE-04-3"   # assessment of the same document
B = "PP-CLUE-02-2"   # body that must carry CS-1
cs1 = seeds["critical_strings"][0]["value"]

r.eq("signpost", lint("CLUE-04", {T: "A chill ran down the corridor at the store."}), [("VL-01", T, "ERROR")])
r.eq("meta phrase", lint("CLUE-04", {T: "This was the real culprit of the leak."}), [("VL-01", T, "ERROR")])
r.eq("innocent clue word allowed", lint("CLUE-04", {T: "No clue to the fault was found in the valve."}), [])
r.eq("llm phrase", lint("CLUE-04", {T: "The valve stood as a testament to wear."}), [("VL-03", T, "ERROR")])
r.eq("llm soft word", lint("CLUE-04", {T: "The valve had a pivotal crack."}), [("VL-03", T, "WARN")])
r.eq("confession", lint("CLUE-04", {T: "I did it and I am sorry."}), [("VL-10", T, "ERROR")])
r.eq("quirk word", lint("CLUE-04", {T: "The quirky clerk logged the valve."}), [("VL-14", T, "WARN")])
r.eq("stock name", lint("CLUE-04", {T: "Signed for by Elias at the desk."}), [("VL-02", T, "WARN")])
r.eq("finding with assessment", lint("CLUE-04", {T: "The seal was probably broken by hand."}), [("VL-07", T, "ERROR")])
r.eq("required string kept", lint("CLUE-02"), [])
r.eq("required string lost", lint("CLUE-02", {B: "FIXTURE text 02 with no time at all."}), [("VL-06", B, "ERROR")])
r.eq("required string altered", lint("CLUE-02", {B: f"FIXTURE text 02 at {cs1[:-1]}9 marmalade."}), [("VL-06", B, "ERROR")])
r.eq("too long", lint("CLUE-04", {T: "word " * 121}), [("VL-12", T, "ERROR")])
r.eq("claims beyond assignment", lint("CLUE-04", mutate=lambda f: f["claims"].update({T: ["FACT-01", "FACT-02"]})), [("VL-11", T, "ERROR")])
r.eq("claims short of assignment", lint("CLUE-04", mutate=lambda f: f["claims"].pop(T)), [("VL-11", T, "WARN")])
fam = bible["cast"][0]["name"]["family"]
drift = fam[:-1] + ("x" if fam[-1] != "x" else "y")
r.eq("name drift", lint("CLUE-04", {T: f"Signed by {drift} at the store."}), [("VL-16", T, "ERROR")])
r.eq("exact name fine", lint("CLUE-04", {T: f"Signed by {fam} at the store."}), [])
r.eq("dashes", lint("CLUE-04", {T: "Seal — intact — noted — again."}), [("VL-15", T, "WARN")])
r.eq("not just but", lint("CLUE-04", {T: "It was not just the seal but the box."}), [("VL-15", T, "WARN")])
r.eq("placeholder inside text", lint("CLUE-04", {T: "See PP-CLUE-05-1 for detail."}), [("KT-FL-01", T, "ERROR")])
r.eq("wrong owner", lint("CLUE-04", mutate=lambda f: f.update({"owner": "CLUE-05"})), [("KT-FL-01", "$", "ERROR")])
r.eq("token missing", lint("CLUE-04", mutate=lambda f: f["fills"].pop(A)), [("KT-FL-01", "$", "ERROR")])

# voice rules on assessments
v = next(d["voice_id"] for d in plan["departments"] if d["id"] == "DEPT-D2")
prof = next(p for p in K.data("voice_matrix")["profiles"] if p["id"] == v)
bad_voice = "Fine."
r.eq("assessment off voice", [x[0] for x in lint("CLUE-04", {A: bad_voice})], ["VL-08"])

# options
desk = [ph for ph in plan["placeholders"] if ph["owner"] == "DESK-01" and ph["kind"] == "option"]
o1, o2 = desk[0]["token"], desk[1]["token"]
r.eq("option far too long", [x[:2] for x in lint("DESK-01", {o1: "Option naming " + fam + " and a great deal more besides here"})],
     [("VL-04", o1), ("VL-04", o2), ("VL-04", desk[2]["token"])])
r.eq("distractor names nobody", lint("DESK-01", {o2: "Option naming nobody at all....."[:len(scenario.make_fill('DESK-01', plan, bible)['fills'][o2])]}),
     [("VL-05", o2, "ERROR")])

# overlap across owners
f1 = scenario.make_fill("CLUE-02", plan, bible)
f2 = scenario.make_fill("CLUE-03", plan, bible)
shared = "the boiler in the east store was cold again by the second bell and nobody had signed the book"
f1["fills"]["PP-CLUE-02-2"] += " " + shared
f2["fills"]["PP-CLUE-03-2"] += " " + shared
r.eq("overlap blames later owner", VL.lint_overlap({"CLUE-02": f1, "CLUE-03": f2}, ["CLUE-02", "CLUE-03"]),
     [{"id": "VL-09", "path": "CLUE-03", "sev": "ERROR"}])
r.eq("no overlap", VL.lint_overlap({"CLUE-02": scenario.make_fill("CLUE-02", plan, bible),
                                    "CLUE-03": scenario.make_fill("CLUE-03", plan, bible)}, ["CLUE-02", "CLUE-03"]), [])

# bible stock names
b = copy.deepcopy(bible)
b["premise"]["hook"] = "FIXTURE hook with Aris Thorne"
r.eq("bible stock name warns", VL.lint_bible_names(b), [{"id": "VL-02", "path": "$", "sev": "WARN"}])

sys.exit(r.finish())
