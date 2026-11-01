"""Tests for kitlib: the seal-safe printer, placeholders, JSON walking. Run: python test_kitlib.py"""
import io
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_test_util import K, Report, reset_data  # noqa: E402

r = Report("test_kitlib")
reset_data()

# --- Out: only IDs, paths, trusted terms and numbers pass
buf = io.StringIO()
out = K.Out(stream=buf, path_keys={"clues", "raw_observation_text"})
r.eq("id passes", out.say("CHECK_FINDING_FAIL", "VL-01", "$.clues[2].raw_observation_text"),
     "CHECK VL-01 FAIL $.clues[2].raw_observation_text")
r.eq("story text withheld", out.say("CHECK_FINDING_FAIL", "Bram did it", "$.clues[0]"),
     "CHECK WITHHELD FAIL $.clues[0]")
r.eq("unknown path key withheld", out.say("CHECK_FINDING_FAIL", "VL-01", "$.secret_story"),
     "CHECK VL-01 FAIL WITHHELD")
r.eq("word-shaped ID withheld", out.say("CHECK_PASS", "BRAM-01"), "CHECK WITHHELD PASS")
r.eq("ID without digit withheld", out.say("CHECK_PASS", "CLUE-AB"), "CHECK WITHHELD PASS")
r.eq("unit ID passes", out.say("CHECK_PASS", "S5-S3-CLUE-07-R1"), "CHECK S5-S3-CLUE-07-R1 PASS")
r.eq("placeholder token passes", out.say("CHECK_PASS", "PP-CLUE-07-2"), "CHECK PP-CLUE-07-2 PASS")
r.eq("option ID passes", out.say("CHECK_PASS", "OPT-Q01-A"), "CHECK OPT-Q01-A PASS")
r.eq("numbers pass", out.say("BUDGET_RUN", 26, 80), "BUDGET run turns 26 of 80")
r.eq("unknown message", out.say("NO_SUCH_MESSAGE", "x"), "MESSAGE WITHHELD")
out.trust(terms=["MASKS"])
r.eq("trusted term passes", out.say("COMPAT_UNAVAILABLE", "PAT-03", "MASKS"), "COMPAT PAT-03 UNAVAILABLE missing MASKS")
r.eq("untrusted term withheld", out.say("COMPAT_UNAVAILABLE", "PAT-03", "masks the murder"), "COMPAT PAT-03 UNAVAILABLE missing WITHHELD")

# --- placeholders
rx = K.placeholder_regex("PP-{owner}-{n}")
m = rx.match("PP-CLUE-07-2")
r.eq("placeholder owner", m.group("owner"), "CLUE-07")
r.eq("placeholder n", m.group("n"), "2")
r.eq("desk owner", rx.match("PP-DESK-01-11").group("owner"), "DESK-01")
r.check("not a placeholder", rx.match("CLUE-07") is None)
find = K.placeholder_search_regex("PP-{owner}-{n}")
r.check("token found inside text", find.search("text PP-CLUE-01-3 more") is not None)
r.check("no false find", find.search("Form record 07") is None)

skel = {"a": "PP-X1-1", "b": [{"c": "PP-X1-2"}, "keep"], "n": 3}
case, placed = K.rebuild_case(skel, {"PP-X1-1": "one", "PP-X1-2": "two"})
r.eq("rebuild values", case, {"a": "one", "b": [{"c": "two"}, "keep"], "n": 3})
r.eq("rebuild paths", placed, {"PP-X1-1": "$.a", "PP-X1-2": "$.b[0].c"})
r.eq("skeleton untouched", skel["a"], "PP-X1-1")
r.eq("token paths", K.token_paths(skel, rx), {"PP-X1-1": ["$.a"], "PP-X1-2": ["$.b[0].c"]})

# --- helpers
r.eq("jpath", K.jpath(["routes", "FACT-01", 0]), "$.routes[*][0]")
r.eq("levenshtein 1", K.levenshtein("fiala", "fialo"), 1)
r.eq("levenshtein cap", K.levenshtein("abc", "abcdefgh", cap=1), 2)
r.eq("words", K.words("It's 12:31, Item FIXTURE-03."), ["it's", "12", "31", "item", "fixture", "03"])
r.check("phrase boundary", K.phrase_in("the clue was here", "clue") and not K.phrase_in("clueless", "clue"))

os.environ["X_API_KEY"] = "s"
os.environ["Y_AUTH_TOKEN"] = "s"
env = K.child_env(K.data("kit_config"))
r.check("api key stripped", "X_API_KEY" not in env and "Y_AUTH_TOKEN" not in env)
r.check("other env kept", "PATH" in env)
del os.environ["X_API_KEY"], os.environ["Y_AUTH_TOKEN"]

# --- every message ID used in code exists in messages.json
import re  # noqa: E402
msgs = set(K.data("messages")["messages"])
used = set()
for p in (K.KIT_DIR / "python").glob("*.py"):
    src = p.read_text(encoding="utf-8")
    used.update(re.findall(r'(?:say|KitError)\(\s*"([A-Z][A-Z_]+)"', src))
    used.update(re.findall(r'"((?:STATUS|BUDGET_STOP|CHECK_FINDING|ABORT)_[A-Z_]+)"', src))
r.eq("all used messages defined", sorted(used - msgs), [])

sys.exit(r.finish())
