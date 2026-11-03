"""Tests for media: the registry, the material model, the checks and the manifest. Run: python test_media.py"""
import copy
import datetime as dt
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_test_util import FIXTURE_ROOT, K, Report, override_data, reset_data  # noqa: E402
import scenario  # noqa: E402
import media as MD  # noqa: E402
from compat_check import run_compat  # noqa: E402
from seed_sampler import sample  # noqa: E402

r = Report("test_media")
reset_data()
seeds = sample(7, run_compat(FIXTURE_ROOT))
bible = scenario.make_bible(seeds)
for i, p in enumerate(bible["cast"]):
    p["appearance"] = f"FIXTURE tall build, cropped grey hair, scar on left hand, orange parka {i:02d}"
base_plan, case, skin = scenario.make_s2(bible, seeds)


def ids(findings):
    return sorted({f["id"] for f in findings if f["sev"] == "ERROR"})


def clue(p, cid):
    return next(c for c in p["clues"] if c["id"] == cid)


def add_ph(p, owner, kind):
    n = 1 + max(int(ph["token"].rsplit("-", 1)[1]) for ph in p["placeholders"] if ph["owner"] == owner)
    tok = f"PP-{owner}-{n}"
    p["placeholders"].append({"token": tok, "owner": owner, "stage": "S3", "slot": kind, "kind": kind,
                              "facts": [], "required_strings": []})
    return tok


def rich_plan():
    """Every artifact family at once: reports in date order, a photo series, a badge, a newspaper, a video."""
    p = copy.deepcopy(base_plan)
    p["media_environment"] = {"climate": "polar", "hemisphere": "north",
                              "cameras": [{"id": "CAM-1", "kind": "film_35mm", "owner": "CHAR-W1"},
                                          {"id": "CAM-2", "kind": "digital"}],
                              "publications": [{"id": "PUB-1", "name": "The Station Bulletin", "founded": "2019-01-01", "cadence_days": 7}]}
    dates = {"CLUE-01": "2026-03-01", "CLUE-05": "2026-03-09", "CLUE-06": "2026-03-04", "CLUE-02": "2026-03-02",
             "CLUE-08": "2026-03-05", "CLUE-04": "2026-03-03", "CLUE-09": "2026-03-07", "CLUE-10": "2026-03-06"}
    for cid, d in dates.items():
        clue(p, cid)["date"] = d
    # three reports, out of ID order but in date order 01, 06, 05
    for cid in ("CLUE-01", "CLUE-05", "CLUE-06"):
        clue(p, cid)["form_id"] = "DF-01"
        body = next(ph["token"] for ph in p["placeholders"] if ph["owner"] == cid and ph["kind"] in ("body", "finding"))
        clue(p, cid)["media"] = {"kind": "MF-05", "regions": {"body": body}}
    # two photographs on one camera, one on another
    for cid, cam, t in (("CLUE-02", "CAM-1", None), ("CLUE-08", "CAM-1", None), ("CLUE-09", "CAM-2", "21:14")):
        clue(p, cid)["form_id"] = "DF-17"
        dep = add_ph(p, cid, "depiction")
        clue(p, cid)["media"] = {"kind": "MF-01", "camera": cam, "depicts": ["CHAR-S1"], "regions": {"depiction": dep}}
        if t:
            clue(p, cid)["media"]["taken_at"] = t
    # a badge
    clue(p, "CLUE-04")["form_id"] = "DF-19"
    clue(p, "CLUE-04")["media"] = {"kind": "MF-03", "depicts": ["CHAR-S2"], "regions": {}}
    # a newspaper page
    clue(p, "CLUE-10")["form_id"] = "DF-18"
    toks = [ph["token"] for ph in p["placeholders"] if ph["owner"] == "CLUE-10"]
    clue(p, "CLUE-10")["media"] = {"kind": "MF-04", "publication": "PUB-1", "regions": {"headline": toks[0], "body": toks[1]}}
    # the one video
    clue(p, "CLUE-07")["form_id"] = "DF-09"
    clue(p, "CLUE-07")["date"] = "2026-03-08"
    dep = add_ph(p, "CLUE-07", "depiction")
    tr = next(ph["token"] for ph in p["placeholders"] if ph["owner"] == "CLUE-07" and ph["kind"] == "body")
    clue(p, "CLUE-07")["media"] = {"kind": "MF-12", "camera": "CAM-2", "taken_at": "03:40", "depicts": ["LOC-1"],
                                   "regions": {"depiction": dep, "transcript": tr}}
    return p


plan = rich_plan()
lim = copy.deepcopy(K.data("limits"))
lim["media"]["max_plates"] = 6
lim["media"]["max_items"] = 12
override_data("limits", lim)

# ---------------------------------------------------------------- checks pass on a valid plan
r.eq("valid rich plan", ids(MD.check_plan_media(plan, bible, seeds)), [])
r.eq("scenario plan", ids(MD.check_plan_media(base_plan, bible, seeds)), [])
r.eq("plan without media", MD.check_plan_media({**base_plan, "clues": [{k: v for k, v in c.items() if k != "media"} for c in base_plan["clues"]]}, bible, seeds), [])

# ---------------------------------------------------------------- the registry is deterministic and consistent
reg = MD.build_registry(plan, bible, seeds)
r.eq("deterministic", MD.build_registry(plan, bible, seeds), reg)
other = dict(seeds, critical_strings=[{"id": "CS-1", "kind": "CSK-TIME", "value": "09:41"}])
r.check("seeds change the numbers", MD.build_registry(plan, bible, other)["items"]["CLUE-01"]["values"]["report_no"]
        != reg["items"]["CLUE-01"]["values"]["report_no"])
r.eq("institution code", reg["institution"]["code"], "FI")

rn = {c: int(reg["items"][c]["values"]["report_no"].rsplit("-", 1)[1]) for c in ("CLUE-01", "CLUE-06", "CLUE-05")}
r.check("report numbers rise with filing date", rn["CLUE-01"] < rn["CLUE-06"] < rn["CLUE-05"])
r.check("report format", all(re.fullmatch(r"FI-26-\d{4}", reg["items"][c]["values"]["report_no"]) for c in rn))
r.check("received on or after filing", all(
    dt.datetime.strptime(reg["items"][c]["values"]["received"], "%d %b %Y") >= dt.datetime.strptime(reg["items"][c]["values"]["filed"], "%d %b %Y")
    for c in rn))

people = reg["people"]
order = sorted(people, key=lambda x: people[x]["issued_iso"])
nums = [int(people[x]["badge_no"].split("-")[1]) for x in order]
r.check("badge numbers follow hiring order", nums == sorted(nums) and len(set(nums)) == len(nums))
b = people["CHAR-S2"]
r.eq("badge shows its person's number", reg["items"]["CLUE-04"]["values"]["badge_no"], b["badge_no"])
iss = dt.date.fromisoformat(b["issued_iso"])
r.eq("badge expiry is issue plus validity", reg["items"]["CLUE-04"]["values"]["expires"], MD.printed_date(iss + dt.timedelta(days=1095)))
r.check("badge issued before the archive", iss < dt.date.fromisoformat(reg["archive_date"]))

news = reg["items"]["CLUE-10"]["values"]
r.eq("dateline weekday", news["dateline"], "Friday 6 March 2026")
r.eq("issue number from founding and cadence", news["issue_line"], f"Vol. 8 No. {(dt.date(2026, 3, 6) - dt.date(2019, 1, 1)).days // 7 + 1}")

f1 = reg["items"]["CLUE-02"]["frame"]
f2 = reg["items"]["CLUE-08"]["frame"]
r.check("frames on one camera rise with time", f1 < f2)
r.eq("film imprint", reg["items"]["CLUE-02"]["values"]["imprint"], "'26 3 2")
r.eq("digital imprint uses the shot time", reg["items"]["CLUE-09"]["values"]["imprint"], "2026/03/07 21:14")
r.check("digital file name", re.fullmatch(r"IMG_\d{4}", reg["items"]["CLUE-09"]["values"]["frame"]) is not None)
r.check("cameras keep separate counters", reg["items"]["CLUE-09"]["frame"] is not None)
r.eq("polar north in March is a short day", reg["items"]["CLUE-02"]["light"], MD.calculus()["light_regimes"]["polar_north"]["shoulder"])
r.eq("polar night in December", MD.light_regime("polar", "north", dt.date(2026, 12, 3), None),
     MD.calculus()["light_regimes"]["polar_north"]["dark"])
r.eq("southern polar night in June", MD.light_regime("polar", "south", dt.date(2026, 6, 3), None),
     MD.calculus()["light_regimes"]["polar_south"]["dark"])
r.check("video timecode", re.fullmatch(r"03:40:\d{2}", reg["items"]["CLUE-07"]["values"]["timecode"]) is not None)
r.check("reports by a person carry their badge", all(
    reg["items"][c]["values"].get("officer") == people.get(clue(plan, c)["author"], {}).get("badge_no")
    for c in rn if clue(plan, c)["author"] in people))

# ---------------------------------------------------------------- the material model: same paper, and wear never hides evidence
forms = MD.forms()
young = MD.material(forms["MF-04"], {}, 30, "temperate", "s", "x")
old = MD.material(forms["MF-04"], {}, 3650, "temperate", "s", "x")
r.check("older newsprint is yellower", old["yellowing"] > young["yellowing"])
r.check("newsprint yellows faster than bond", young["yellowing"] > MD.material(forms["MF-05"], {}, 30, "temperate", "s", "x")["yellowing"])
r.eq("material is deterministic", MD.material(forms["MF-04"], {}, 365, "polar", "s", "x"), MD.material(forms["MF-04"], {}, 365, "polar", "s", "x"))
floor = MD.calculus()["fairness"]["legibility_floor"]
worst = []
for form_id in ("MF-01", "MF-04", "MF-05", "MF-06", "MF-07", "MF-11"):
    for clim in MD.calculus()["climates"]:
        for days in (0, 400, 4000, 40000):
            m = MD.material(forms[form_id], {"handling": 5, "storage": "pinned"}, days, clim, "s", form_id + clim)
            worst.append(m["legibility"])
r.check("legibility never below the floor", min(worst) >= floor)
r.check("the floor was enforced somewhere", any(
    MD.material(forms["MF-07"], {"handling": 5, "storage": "pinned"}, 40000, "tropical", "s", "q")["clamped"] for _ in [0]))
sk = [MD.material(forms["MF-05"], {}, 10, "polar", "s", f"i{k}")["scan"]["skew_deg"] for k in range(50)]
r.check("scan skew within limits", all(abs(x) <= 1.5 for x in sk) and len(set(sk)) > 10)
r.check("screens do not age", MD.material(forms["MF-10"], {}, 9999, "tropical", "s", "x")["legibility"] == 1.0)


# ---------------------------------------------------------------- each bad declaration fails its own check
def mut(fn, b=None):
    p = copy.deepcopy(plan)
    fn(p)
    return ids(MD.check_plan_media(p, b or bible, seeds))


r.eq("unknown media form", mut(lambda p: clue(p, "CLUE-01")["media"].update({"kind": "MF-99"})), ["KT-MD-01"])
r.eq("form cannot dress this document", mut(lambda p: clue(p, "CLUE-01").update({"form_id": "DF-02"})), ["KT-MD-01"])
r.eq("photo without camera", mut(lambda p: clue(p, "CLUE-02")["media"].pop("camera")), ["KT-MD-01"])
r.eq("digital photo needs a time", mut(lambda p: clue(p, "CLUE-09")["media"].pop("taken_at")), ["KT-MD-01"])
r.eq("bad time", mut(lambda p: clue(p, "CLUE-09")["media"].update({"taken_at": "25:00"})), ["KT-MD-01"])
r.eq("depiction region missing", mut(lambda p: clue(p, "CLUE-02")["media"].update({"regions": {}})), ["KT-MD-01", "KT-MD-09"])
r.eq("region mapped to another document", mut(lambda p: clue(p, "CLUE-10")["media"]["regions"].update({"body": "PP-CLUE-01-1"})), ["KT-MD-01"])
r.eq("badge shows exactly one person", mut(lambda p: clue(p, "CLUE-04")["media"].update({"depicts": ["CHAR-S1", "CHAR-S2"]})), ["KT-MD-01"])
r.eq("newspaper without publication", mut(lambda p: clue(p, "CLUE-10")["media"].pop("publication")), ["KT-MD-01"])
r.eq("publication founded after the issue", mut(lambda p: p["media_environment"]["publications"][0].update({"founded": "2027-01-01"})), ["KT-MD-01"])
r.eq("handling out of range", mut(lambda p: clue(p, "CLUE-01")["media"].update({"handling": 9})), ["KT-MD-01"])
nob = copy.deepcopy(bible)
nob["cast"][0].pop("appearance")
r.eq("person in a photo needs a likeness", mut(lambda p: None, nob), ["KT-MD-03"])
lim2 = copy.deepcopy(K.data("limits"))
lim2["media"]["max_plates"] = 2
override_data("limits", lim2)
r.eq("plate cap", mut(lambda p: None), ["KT-MD-02"])
override_data("limits", lim)


def two_videos(p):
    clue(p, "CLUE-03")["form_id"] = "DF-12"
    dep = add_ph(p, "CLUE-03", "depiction")
    tr = next(ph["token"] for ph in p["placeholders"] if ph["owner"] == "CLUE-03" and ph["kind"] == "body")
    clue(p, "CLUE-03")["media"] = {"kind": "MF-12", "camera": "CAM-2", "taken_at": "04:00", "regions": {"depiction": dep, "transcript": tr}}


r.eq("at most one video", mut(two_videos), ["KT-MD-02"])
lim3 = copy.deepcopy(lim)
lim3["media"]["video"]["min_enforced"] = True
override_data("limits", lim3)
r.eq("exactly one video when enforced", ids(MD.check_plan_media(base_plan, bible, seeds)), ["KT-MD-02"])
override_data("limits", lim)
r.eq("unknown climate", mut(lambda p: p["media_environment"].update({"climate": "lunar"})), ["KT-MD-07"])
r.eq("camera too modern for the era", mut(lambda p: [c.update({"date": "1980-03-04"}) for c in p["clues"]]), ["KT-MD-01", "KT-MD-07"])
r.eq("bad institution code", mut(lambda p: p["media_environment"].update({"institution_code": "x1"})), ["KT-MD-07"])
r.eq("publication name not plain", mut(lambda p: p["media_environment"]["publications"][0].update({"name": "Bulletin™"})), ["KT-MD-07"])
same = reg["items"]["CLUE-05"]["values"]["report_no"]
r.eq("anomaly must differ from the calculation", mut(lambda p: clue(p, "CLUE-05")["media"].update(
    {"anomaly": {"value_key": "report_no", "value": same, "fact": clue(p, "CLUE-05")["facts"][0]}})), ["KT-MD-08"])
r.eq("anomaly must carry the document's fact", mut(lambda p: clue(p, "CLUE-05")["media"].update(
    {"anomaly": {"value_key": "report_no", "value": "FI-26-0001", "fact": "FACT-99"}})), ["KT-MD-08"])
r.eq("valid anomaly", mut(lambda p: clue(p, "CLUE-05")["media"].update(
    {"anomaly": {"value_key": "report_no", "value": "FI-26-0001", "fact": clue(p, "CLUE-05")["facts"][0]}})), [])
r.eq("stray depiction placeholder", mut(lambda p: add_ph(p, "CLUE-03", "depiction")), ["KT-MD-09"])

ap = copy.deepcopy(plan)
clue(ap, "CLUE-05")["media"]["anomaly"] = {"value_key": "report_no", "value": "FI-26-0001", "fact": clue(ap, "CLUE-05")["facts"][0]}
areg = MD.build_registry(ap, bible, seeds)
r.eq("anomaly replaces only its value", areg["items"]["CLUE-05"]["values"]["report_no"], "FI-26-0001")
r.eq("other reports unchanged by an anomaly", areg["items"]["CLUE-01"]["values"], reg["items"]["CLUE-01"]["values"])

# ---------------------------------------------------------------- S3 and gate lint
vals = MD.required_values("CLUE-01", reg)
good = {"owner": "CLUE-01", "fills": {"a": "Header " + " | ".join(vals.values()), "b": "Text."}, "claims": {}}
r.eq("all values present", ids(MD.lint_fill(good, "CLUE-01", plan, reg)), [])
miss = copy.deepcopy(good)
miss["fills"]["a"] = "Header without the number"
r.eq("missing value", ids(MD.lint_fill(miss, "CLUE-01", plan, reg)), ["KT-MD-04"])
inv = copy.deepcopy(good)
inv["fills"]["b"] = "See report FI-26-0002 for details."
r.eq("invented series number", ids(MD.lint_fill(inv, "CLUE-01", plan, reg)), ["KT-MD-05"])
ref = copy.deepcopy(good)
ref["fills"]["b"] = "See report " + reg["items"]["CLUE-05"]["values"]["report_no"] + " for details."
r.eq("citing a real number elsewhere is fine", ids(MD.lint_fill(ref, "CLUE-01", plan, reg)), [])
wd = copy.deepcopy(good)
wd["fills"]["b"] = "Logged on Monday 6 March 2026."
r.eq("wrong weekday", ids(MD.lint_fill(wd, "CLUE-01", plan, reg)), ["KT-MD-06"])
wd["fills"]["b"] = "Logged on Friday, March 6, 2026."
r.eq("right weekday, either order", ids(MD.lint_fill(wd, "CLUE-01", plan, reg)), [])
r.eq("plain documents carry nothing extra", MD.lint_fill({"fills": {"a": "x"}}, "CLUE-03", plan, reg), [])
cons = MD.lint_consistency({"CLUE-03": {"fills": {"a": "badge FI-9999"}}, "CLUE-02": {"fills": {"a": "fine"}}}, reg)
r.eq("gate blames the owner", [(f["id"], f["path"]) for f in cons], [("KT-MD-05", "CLUE-03")])
r.eq("no registry, no media lint", MD.lint_fill(miss, "CLUE-01", plan, None), [])

# ---------------------------------------------------------------- S3 brief
brief = MD.brief_for("CLUE-01", plan, bible, reg)
r.check("brief lists every printed value", all(v in brief for v in vals.values()))
r.check("brief names the object", "incident or arrest report form" in brief)
r.check("photo brief asks for a camera's-eye depiction", "Only what a camera could see" in MD.brief_for("CLUE-02", plan, bible, reg))
r.check("photo brief carries the light", reg["items"]["CLUE-02"]["light"] in MD.brief_for("CLUE-02", plan, bible, reg))
r.check("plain documents say so", "plain text" in MD.brief_for("CLUE-03", plan, bible, reg))

# ---------------------------------------------------------------- the manifest is player-safe
fills = {}
for owner in {ph["owner"] for ph in plan["placeholders"] if ph["stage"] == "S3"}:
    fills[owner] = {"owner": owner, "fills": {ph["token"]: f"FIXTURE words for {ph['kind']} " * 4
                                              for ph in plan["placeholders"] if ph["owner"] == owner}, "claims": {}}
placed = {ph["token"]: f"$.clues[0].x{i}" for i, ph in enumerate(plan["placeholders"]) if ph["kind"] != "depiction"}
man = MD.build_manifest(plan, bible, fills, reg, placed)
blob = json.dumps(man)
r.check("manifest holds no fact IDs", "FACT-" not in blob)
r.check("manifest holds no roles, tiers, routes or anomaly flags",
        not any(k in blob for k in ('"role": "solution"', '"tier"', '"routes"', '"anomaly"', "herring", "KEY_CANARY", scenario.KEY_CANARY)))
r.check("manifest holds no bible statements", "FIXTURE statement" not in blob)
r.eq("artifact count", MD.summary(man), (9, 4, 1))
photo = next(p for p in man["plates"] if p["for"] == "CLUE-09")
r.eq("plate text is only what the artifact prints", sorted(photo["text_in_image"]), sorted(reg["items"]["CLUE-09"]["values"].values()))
r.check("plate subject carries the likeness", photo["subjects"][0]["likeness"] == bible["cast"][0]["appearance"])
r.check("same person, same likeness in every plate", len({json.dumps(s) for p in man["plates"] for s in p["subjects"] if s["id"] == "CHAR-S1"}) == 1)
r.check("alt text is the depiction", next(i for i in man["items"] if i["id"] == "CLUE-02")["alt"].startswith("FIXTURE words for depiction"))
vid = next(i for i in man["items"] if i["family"] == "video")
r.check("video duration from transcript length", re.fullmatch(r"\d{2}:\d{2}", vid["duration"]) is not None)
r.check("plate seeds are stable", MD.build_manifest(plan, bible, fills, reg, placed)["plates"] == man["plates"])

# ---------------------------------------------------------------- printing stays sealed
buf = io.StringIO()
line = K.Out(stream=buf).say("MEDIA_COUNTS", *MD.summary(man))
r.eq("summary prints counts only", line, "MEDIA artifacts 9 plates 4 video 1")
r.check("every media ID prints", "WITHHELD" not in K.Out(stream=io.StringIO()).say("ABORT_LINE", "KT-MD-05"))

reset_data()
sys.exit(r.finish())
