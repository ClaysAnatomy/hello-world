"""Tests for brief_builder: template filling and stage isolation. Run: python test_brief_builder.py"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_test_util import K, Report, reset_data  # noqa: E402
import brief_builder as BB  # noqa: E402

r = Report("test_brief_builder")
reset_data()

r.eq("render fills tokens", BB.render("A {{X}} B {{Y_2}}", {"X": "1", "Y_2": "2"}), "A 1 B 2")
try:
    BB.render("A {{MISSING}}", {})
    r.check("missing token raises", False)
except K.KitError as e:
    r.eq("missing token message", e.msg_id, "ERR_TEMPLATE_TOKEN")
r.eq("single braces untouched", BB.render("PP-{owner}-{n} {{A}}", {"A": "x"}), "PP-{owner}-{n} x")

hdr = BB.header()
r.check("header has seal and bans", "## The seal" in hdr and "BL-SIGNPOST (never)" in hdr and "{{" not in hdr)

# every template token is one the builder supplies somewhere
src = (K.KIT_DIR / "python" / "brief_builder.py").read_text(encoding="utf-8")
supplied = set(re.findall(r'"([A-Z][A-Z0-9_]+)":', src)) | set(re.findall(r'ctx\["([A-Z_]+)"\]', src)) | {"INPUT_FILES", "OUTPUT_FILES"}
for p in sorted(K.PROMPTS_DIR.glob("*.md")):
    tokens = set(BB.TOKEN_RX.findall(p.read_text(encoding="utf-8")))
    r.eq(f"tokens supplied for {p.name}", sorted(tokens - supplied), [])

# check lists are stage-specific
r.check("S1 lists bible checks only", "KT-BI-01" in BB.check_list("S1") and "VL-" not in BB.check_list("S1"))
r.check("S3 omits option checks", "VL-04" not in BB.check_list("S3") and "VL-07" in BB.check_list("S3"))
r.check("S4 omits voice checks", "VL-08" not in BB.check_list("S4") and "VL-04" in BB.check_list("S4"))

# voice text quotes nonsense exemplars only
vt = BB.voice_profile_text(K.data("voice_matrix")["profiles"][0])
r.check("voice text", vt.startswith("Voice V1:") and "FIXTURE" in vt)
r.check("forms table rows", BB.forms_table().count("\n| DF-") == len(K.data("document_forms")["forms"]))

sys.exit(r.finish())
