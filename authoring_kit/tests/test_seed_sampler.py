"""Tests for seed_sampler and ledger. Run: python test_seed_sampler.py"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_test_util import FIXTURE_ROOT, K, Report, reset_data  # noqa: E402
from compat_check import run_compat  # noqa: E402
from ledger import Ledger, seed_items  # noqa: E402
from seed_sampler import _sound_key, sample  # noqa: E402

r = Report("test_seed_sampler")
reset_data()
compat = run_compat(FIXTURE_ROOT)

s7 = sample(7, compat)
r.eq("deterministic", sample(7, compat), s7)
r.eq("seed 7 exact", {k: s7[k] for k in ("patterns", "mechanism", "red_herring", "stakes", "human_question", "irony", "setting_texture", "name_pool", "suspect_count", "cast_total", "dept_mix")},
     {"patterns": ["PAT-05"], "mechanism": "MECH-09", "red_herring": "RH-05", "stakes": "STK-03",
      "human_question": "HQ-08", "irony": "IR-06", "setting_texture": "TX-03", "name_pool": "NP-3",
      "suspect_count": 3, "cast_total": 6, "dept_mix": s7["dept_mix"]})
r.eq("seed 7 names", [f"{n['given']} {n['family']}" for n in s7["cast_names"]],
     ["Kerstin Strand", "Gunnar Olsen", "Henk Lindqvist", "Joost Groot", "Ingrid Mulder", "Fenna Aalders"])
r.eq("seed 7 strings", [c["value"] for c in s7["critical_strings"]], ["07:39", "12:31"])

bans = {t.lower() for c in K.data("ban_lists")["categories"] if c["id"].startswith("BL-NAMES") for t in c["terms"]}
unavailable = {"PAT-12"}
lim = K.data("limits")["budget"]
for seed in range(200):
    s = sample(seed, compat)
    tag = f"seed {seed}"
    g = [n["given"] for n in s["cast_names"]]
    f = [n["family"] for n in s["cast_names"]]
    ok = (len({x[0] for x in g}) == len(g) and len({x[0] for x in f}) == len(f)
          and len({_sound_key(x) for x in f}) == len(f)
          and not ({x.lower() for x in g + f} & bans)
          and not (set(s["patterns"]) & unavailable)
          and 1 <= len(s["patterns"]) <= lim["max_patterns"]
          and lim["min_suspects"] <= s["suspect_count"] <= lim["max_suspects"]
          and s["cast_total"] <= lim["max_cast_total"]
          and len(s["critical_strings"]) == lim["max_critical_strings"]
          and len(set(s["dept_mix"])) == len(s["dept_mix"]))
    if len(s["patterns"]) == 2:
        p = {x["id"]: x for x in K.data("patterns")["patterns"]}
        ok = ok and s["patterns"][1] in p[s["patterns"][0]]["combines_with"]
    for c in s["critical_strings"]:
        v = c["value"]
        if c["kind"] == "CSK-TIME":
            ok = ok and len(v) == 5 and v[2] == ":" and int(v[3:]) % 5 != 0
        else:
            ok = ok and len(v) == 6 and v[1] == "-" and v[2:].isdigit()
    r.check(f"constraints {tag}", ok)

# no available pattern is an error
try:
    sample(1, {"patterns": {}})
    r.check("no patterns raises", False)
except K.KitError as e:
    r.eq("no patterns message", e.msg_id, "ERR_NO_PATTERNS")

# ledger: novelty pushes recent choices away
led = Ledger(None, salt="00")
counts_before = sum(1 for sd in range(300) if "PAT-05" in sample(sd, compat, led)["patterns"])
for _ in range(3):
    led.append("r", [("pattern", "PAT-05")])
counts_after = sum(1 for sd in range(300) if "PAT-05" in sample(sd, compat, led)["patterns"])
r.check("ledger lowers recent pattern", counts_after < counts_before / 2)

# taste weights pull choices toward liked seeds
heavy = {"weights": {"PAT-01": 2.0}}
light = {"weights": {"PAT-01": 0.3}}
up = sum(1 for sd in range(300) if "PAT-01" in sample(sd, compat, None, heavy)["patterns"])
down = sum(1 for sd in range(300) if "PAT-01" in sample(sd, compat, None, light)["patterns"])
r.check("taste weight raises and lowers", up > down)

# ledger file: salted hashes only, round trip
tmp = Path(tempfile.mkdtemp())
lp = tmp / "state" / "ledger.json"
L = Ledger.load(lp)
L.append("run1", seed_items(s7))
L.save()
text = lp.read_text(encoding="utf-8")
r.check("ledger holds no plain IDs", "PAT-05" not in text and "Fiala" not in text and "MECH-06" not in text)
L2 = Ledger.load(lp)
r.check("ledger round trip", L2.recent("pattern", "PAT-05", 6) and not L2.recent("pattern", "PAT-01", 6))
r.check("ledger window", not L2.recent("pattern", "PAT-05", 0))
r.eq("hash stable", Ledger(None, salt="ab").h("pattern", "PAT-01"), Ledger(None, salt="ab").h("pattern", "PAT-01"))
r.eq("seed items count", len(seed_items(s7)), 1 + 7 + 12)

sys.exit(r.finish())
