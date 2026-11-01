"""Tests for compat_check against the nonsense fixture engine. Run: python test_compat_check.py"""
import io
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_test_util import FIXTURE_ROOT, K, Report, reset_data  # noqa: E402
import compat_check as CC  # noqa: E402

r = Report("test_compat_check")
reset_data()

EXPECTED = """COMPAT PAT-01 AVAILABLE
COMPAT PAT-02 AVAILABLE
COMPAT PAT-03 AVAILABLE
COMPAT PAT-04 AVAILABLE
COMPAT PAT-05 AVAILABLE
COMPAT PAT-06 UNAVAILABLE missing aliases
COMPAT PAT-07 UNAVAILABLE missing aliases
COMPAT PAT-08 AVAILABLE
COMPAT PAT-09 AVAILABLE
COMPAT PAT-10 AVAILABLE
COMPAT PAT-11 AVAILABLE
COMPAT PAT-12 UNAVAILABLE missing accepted_fragment_orders
COMPAT PAT-13 AVAILABLE
COMPAT PAT-14 AVAILABLE
COMPAT PAT-15 AVAILABLE
COMPAT PAT-16 AVAILABLE
COMPAT 13 of 16 patterns available
COMPAT engine rules found 3
COMPAT prose-like schema fields 6
"""

rep = CC.run_compat(FIXTURE_ROOT)
buf = io.StringIO()
code = CC.print_report(rep, K.Out(stream=buf))
r.eq("exit code", code, 0)
r.eq("exact output", buf.getvalue(), EXPECTED)
r.eq("rule ids", rep["rule_ids"], ["DK-01", "FP-01", "FP-02"])
r.eq("masks resolved", rep["capabilities"]["CAP-03"], "MASKS")
r.eq("defeat resolved", rep["capabilities"]["CAP-05"], "defeaters")
r.eq("time resolved", rep["capabilities"]["CAP-08"], "record_date")
r.eq("aliases missing", rep["capabilities"]["CAP-10"], None)
r.check("property names collected", "raw_observation_text" in rep["property_names"])
r.eq("engine files hashed", sorted(rep["engine_files"]), [
    "engine/contract/bundle_contract.json", "engine/schemas/case.v0.2.json",
    "engine/schemas/skin.v0.2.json", "engine/schemas/vocabulary.json"])

# missing schema is a setup error
tmp = Path(tempfile.mkdtemp())
try:
    empty = tmp / "p"
    shutil.copytree(FIXTURE_ROOT, empty)
    for f in (empty / "engine" / "schemas").glob("case*.json"):
        f.unlink()
    rep2 = CC.run_compat(empty)
    buf = io.StringIO()
    r.eq("missing schema exit", CC.print_report(rep2, K.Out(stream=buf)), 2)
    r.eq("missing schema line", buf.getvalue(), "COMPAT FAIL KT-CP-01\n")
    # a vocabulary without MASKS/REFRAMES makes those patterns unavailable
    full = tmp / "q"
    shutil.copytree(FIXTURE_ROOT, full)
    sch = full / "engine" / "schemas" / "case.v0.2.json"
    sch.write_text(sch.read_text().replace('"MASKS", ', ""), encoding="utf-8")
    voc = full / "engine" / "schemas" / "vocabulary.json"
    voc.write_text(voc.read_text().replace('"MASKS", ', ""), encoding="utf-8")
    rep3 = CC.run_compat(full)
    r.eq("PAT-02 needs MASKS", rep3["patterns"]["PAT-02"], {"available": False, "missing": ["CAP-03"]})
    r.eq("PAT-01 unaffected", rep3["patterns"]["PAT-01"]["available"], True)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(r.finish())
