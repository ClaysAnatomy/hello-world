"""Tests for repair_builder, budget_guard and taste_bridge. Run: python test_repair_budget_taste.py"""
import copy
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_test_util import K, Report, override_data, reset_data  # noqa: E402
import repair_builder as RB  # noqa: E402
import taste_bridge as TB  # noqa: E402
from budget_guard import Budget  # noqa: E402

r = Report("test_repair_budget_taste")
reset_data()
RULES = ["FP-01", "FP-02", "DK-01", "R09"]

# ---- engine output parsing: IDs and paths only
out = "FP-01 PASS\nFP-02 FAIL $.clues[3].raw_observation_text\nR09 FAIL\nDK-01 PASS\nsummary: 2 failed\n"
r.eq("parse fails", RB.parse_engine_output(out, 1, "CHK-1", RULES),
     [{"id": "FP-02", "path": "$.clues[3].raw_observation_text", "sev": "ERROR"}, {"id": "R09", "path": "$", "sev": "ERROR"}])
r.eq("tolerated rule dropped", RB.parse_engine_output(out, 1, "CHK-1", RULES, ["R09"]),
     [{"id": "FP-02", "path": "$.clues[3].raw_observation_text", "sev": "ERROR"}])
r.eq("only tolerated failures", RB.parse_engine_output("R09 FAIL\n", 1, "CHK-1", RULES, ["R09"]), [])
r.eq("crash without IDs", RB.parse_engine_output("Traceback ...\n", 1, "CHK-1", RULES), [{"id": "CHK-1", "path": "$", "sev": "ERROR"}])
r.eq("unknown failing line", RB.parse_engine_output("ZZ-9 FAIL\n", 1, "CHK-1", RULES), [{"id": "CHK-1", "path": "$", "sev": "ERROR"}])
r.eq("clean pass", RB.parse_engine_output("FP-01 PASS\n", 0, "CHK-1", RULES), [])
r.eq("id boundary", RB.parse_engine_output("FP-011 FAIL\n", 1, "CHK-1", ["FP-01"]), [{"id": "CHK-1", "path": "$", "sev": "ERROR"}])

# ---- repair decisions
f_a = [{"id": "VL-01", "path": "PP-X1-1", "sev": "ERROR"}]
f_b = [{"id": "VL-06", "path": "PP-X1-1", "sev": "ERROR"}]
r.eq("first failure repairs", RB.decide(None, f_a, 0), RB.REPAIR)
r.eq("same ID again aborts", RB.decide({"history": [["VL-01"]], "round": 0}, f_a, 1), RB.ABORT_REPEAT)
r.eq("new ID repairs again", RB.decide({"history": [["VL-01"]], "round": 0}, f_b, 1), RB.REPAIR)
r.eq("cap reached", RB.decide({"history": [["VL-01"], ["VL-06"]], "round": 1}, [{"id": "VL-12", "path": "$", "sev": "ERROR"}], 2), RB.ABORT_CAP)
table = RB.failures_table(f_a + [{"id": "FP-02", "path": "$.clues[0]", "sev": "ERROR"}, {"id": "VL-03", "path": "x", "sev": "WARN"}],
                          {"FP-02": "Fixture rule FP-02: nonsense requirement."})
r.eq("failures table", table, "| Check | Where | Requirement |\n|---|---|---|\n"
     "| VL-01 | PP-X1-1 | Remove signposting phrases and puzzle vocabulary from player-facing text. |\n"
     "| FP-02 | $.clues[0] | Fixture rule FP-02: nonsense requirement. |")

# ---- budget
state = {}
b = Budget(state)
r.eq("can start", b.can_start("S1"), (True, ""))
b.record("S1", None)
r.eq("unreported turns charge the cap", b.stage_turns("S1"), 6)
r.eq("stage cap hit", b.can_start("S1"), (False, "STAGE"))
b.record("S3", 2, 0.05)
r.eq("reported turns", b.stage_turns("S3"), 2)
r.eq("run turns", b.run_turns(), 8)
lim = copy.deepcopy(K.data("limits"))
lim["turns"]["run_cap"] = 10
override_data("limits", lim)
b2 = Budget(state)
r.eq("run cap hit", b2.can_start("S3"), (False, "RUN"))
lim["turns"]["run_cap"] = 80
lim["cost_usd_unverified"]["run_cap"] = 0.04
override_data("limits", lim)
r.eq("cost cap hit when costs are reported", Budget(state).can_start("S3"), (False, "RUN"))
reset_data()
buf = io.StringIO()
Budget(state).report(K.Out(stream=buf), "S3")
r.eq("budget prints turns only", buf.getvalue(), "BUDGET S3 turns 2 of 36\nBUDGET run turns 8 of 80\n")

# ---- taste
form = K.data("feedback_form")
seeds = {"patterns": ["PAT-05", "PAT-11"], "mechanism": "MECH-06", "red_herring": "RH-03", "stakes": "STK-02",
         "human_question": "HQ-08", "irony": "IR-01", "setting_texture": "TX-04", "name_pool": "NP-2"}
r.eq("valid answers", TB.validate_answers({"answers": {"FB-02": 5, "FB-07": 1}, "numbers": {"FB-N1": 90}}, form), [])
r.eq("text refused", TB.validate_answers({"answers": {"FB-02": "loved it"}}, form), ["FB-02"])
r.eq("out of range", TB.validate_answers({"answers": {"FB-02": 9}}, form), ["FB-02"])
r.eq("unknown key", TB.validate_answers({"notes": "x"}, form), ["FB-00"])
p1 = TB.apply({}, {"answers": {"FB-02": 5, "FB-07": 1, "FB-08": 5}}, seeds)
r.eq("taste update", p1, {"version": 1, "cases": 1, "weights": {"PAT-05": 1.15, "PAT-11": 1.15, "RH-03": 0.85}})
p2 = TB.apply(p1, {"answers": {"FB-02": 3}}, seeds)
r.eq("neutral answer keeps weights", p2["weights"], p1["weights"])
p3 = p1
for _ in range(40):
    p3 = TB.apply(p3, {"answers": {"FB-02": 5}}, seeds)
r.eq("weights capped", p3["weights"]["PAT-05"], K.data("limits")["taste"]["max_weight"])

sys.exit(r.finish())
