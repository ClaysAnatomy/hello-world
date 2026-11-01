"""Tests for placeholder_probe on the fake engine. Run: python test_probe.py"""
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_test_util import FIXTURE_ROOT, K, Report, reset_data  # noqa: E402
import placeholder_probe as PP  # noqa: E402

r = Report("test_probe")
reset_data()
case = FIXTURE_ROOT / "engine" / "fixtures" / "CASE-FIX-01" / "case.json"
skin = FIXTURE_ROOT / "engine" / "fixtures" / "skins" / "SKIN-FIX_A.json"

rep = PP.run_probe(FIXTURE_ROOT, case, skin)
r.eq("prose fields replaced", rep["replaced"], 2)
r.eq("rule that needs real prose found", rep["placeholder_only"], ["FP-03"])
r.eq("clean fixture has no base failures", rep["base_failures"], [])

obj = {"record_title": "a b", "lines": ["x y", "z w"], "clue_id": "CLUE-01", "nested": [{"text": "q r"}], "n": 3}
counter = [0]
PP.placeholderise(obj, ("_title",), {"lines", "text"}, counter)
r.eq("placeholderise", obj, {"record_title": "PP-PROBE-1", "lines": ["PP-PROBE-2", "PP-PROBE-3"], "clue_id": "CLUE-01",
                             "nested": [{"text": "PP-PROBE-4"}], "n": 3})

import contextlib  # noqa: E402
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    code = PP.main(["--root", str(FIXTURE_ROOT), "--case", str(case), "--skin", str(skin)])
r.eq("probe exit", code, 0)
r.eq("probe output", buf.getvalue(), "PROBE prose fields replaced 2\nPROBE FP-03 fails only with placeholders\n")

# a fixture that already fails is reported as a base failure, not a placeholder effect
tmp = Path(tempfile.mkdtemp())
try:
    bad = json.loads(case.read_text())
    bad["clues"][0]["record_date"] = "FORCE-FAIL-FP02"
    bp = tmp / "bad.json"
    bp.write_text(json.dumps(bad))
    rep2 = PP.run_probe(FIXTURE_ROOT, bp, skin)
    r.eq("base failure separated", (rep2["base_failures"], rep2["placeholder_only"]), (["FP-02"], ["FP-03"]))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(r.finish())
