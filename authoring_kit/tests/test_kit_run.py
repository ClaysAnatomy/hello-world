"""End-to-end tests for kit_run with the fake engine and fake agent.

Covers Mode A and Mode B, repair success, abort on repeat, abort at the cap,
budget stop, engine-rule failure and repair, engine drift, setup errors, and
canary tests proving planted strings never reach the screen, the logs, the
ledger, the project tree, or the stage folders that must not see them.

Run: python test_kit_run.py            (compare with the golden transcript)
     python test_kit_run.py --regold   (rewrite the golden transcript)
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_test_util import K, Report, Sandbox, file_contains, files_under, override_data  # noqa: E402
import scenario  # noqa: E402
from scenario import CANARY, KEY_CANARY  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "golden_mode_a.txt"
r = Report("test_kit_run")


def new(mode_a=True, usage_json=True, seed=7, overrides=None, review=False):
    sb = Sandbox(mode_a=mode_a, usage_json=usage_json)
    extra = ["--root", str(sb.root), "--seed", str(seed)] + (["--review"] if review else [])
    code, out = sb.kit("init", *extra)
    assert code == 0, out
    scenario.stage_all(sb.agent_dir, sb.seeds(), overrides)
    return sb, out


# ------------------------------------------------------------------ 1. happy path, Mode A
sb, init_out = new()
try:
    code, run_out = sb.kit("next", "--all")
    r.eq("mode A next exit", code, 0)
    code, fin_out = sb.kit("finish")
    r.eq("finish exit", code, 0)
    transcript = init_out + "--- next --all\n" + run_out + "--- finish\n" + fin_out
    if "--regold" in sys.argv:
        GOLDEN.write_text(transcript, encoding="utf-8")
    r.eq("golden transcript", transcript, GOLDEN.read_text(encoding="utf-8"))
    r.check("finish pass line", fin_out.strip().endswith("FINISH PASS"))
    state = json.loads((sb.ws / "checkpoints" / "state.json").read_text(encoding="utf-8"))
    r.eq("status finished", state["status"], "finished")
    r.eq("turns from usage report", state["budget"]["turns"]["S3"], 20)
    # canaries
    everything = init_out + run_out + fin_out
    r.check("canary not on screen", CANARY not in everything and KEY_CANARY not in everything)
    for name in ("state.json", "history.json", "compat.json", "seeds.json"):
        r.check(f"canary not in {name}", not file_contains(sb.ws / "checkpoints" / name, CANARY))
    r.check("canary not in claims", not file_contains(sb.ws / "claims.json", CANARY))
    outside = [p for p in files_under(sb.root) if file_contains(p, CANARY) or file_contains(p, KEY_CANARY)]
    r.eq("canary not in project tree", outside, [])
    ledger = sb.root / "authoring_kit" / "state" / "ledger.json"
    r.check("ledger written", ledger.is_file())
    seeds = sb.seeds()
    r.check("ledger has no plain seeds", not any(file_contains(ledger, x) for x in seeds["patterns"] + [seeds["cast_names"][0]["family"]]))
    blind = [p for d in (sb.ws / "stages").iterdir() if d.name.startswith(("S3-", "S4"))
             for p in files_under(d) if file_contains(p, KEY_CANARY)]
    r.eq("answer key never in S3 or S4 folders", blind, [])
    s3_inputs = sorted({p.name for d in (sb.ws / "stages").iterdir() if d.name.startswith("S3-") for p in (d / "inputs").iterdir()})
    r.eq("S3 folders hold only the fill schema", s3_inputs, ["fill.schema.json"])
    s4 = (sb.ws / "stages" / "S4" / "prompt.md").read_text(encoding="utf-8")
    r.check("S4 brief hides correctness", '"correct"' not in s4 and "correct:" not in s4.lower().replace("correct.", ""))
    r.check("all prompts rendered", not any("{{" in p.read_text(encoding="utf-8") for p in (sb.ws / "stages").rglob("prompt.md")))
    calls = sb.calls()
    r.eq("agent saw no secret variables", sorted({v for c in calls for v in c["secret_vars"]}), [])
    r.check("prompt sent on stdin", all(c["stdin_chars"] > 500 for c in calls))
    r.eq("max turns passed to agent", calls[0]["argv"], ["6"])
    claims = json.loads((sb.ws / "claims.json").read_text(encoding="utf-8"))["claims"]
    r.check("claims are paths and IDs", all(c["path"].startswith("$.") and all(f.startswith("FACT-") for f in c["facts"]) for c in claims))
    case = json.loads((sb.ws / "case.json").read_text(encoding="utf-8"))
    r.check("no placeholder left", not any(s.startswith("PP-") for s in K.string_leaves(case)))
finally:
    sb.close()

# ------------------------------------------------------------------ 2. Mode B
sb, _ = new(mode_a=False)
try:
    code, out = sb.kit("next")
    r.eq("mode B next", (code, out), (3, "NEXT S1 READY\nPROMPT stages/S1/prompt.md\n"))
    code, out = sb.kit("next")
    r.eq("mode B waiting", (code, out), (3, "Stage S1 is waiting for a check. Run check.\n"))
    for name in ("bible.json",):
        (sb.ws / "stages" / "S1" / name).write_bytes((sb.agent_dir / "S1" / name).read_bytes())
    code, out = sb.kit("check")
    r.eq("mode B check", (code, out), (0, "CHECK errors 0 warnings 0\nCHECK S1 PASS\n"))
    code, out = sb.kit("check")
    r.eq("nothing to check", (code, out), (3, "No stage is waiting for a check. Run next first.\n"))
    code, out = sb.kit("status")
    r.eq("status", (code, out), (0, "STATUS units done 1 of 2\nSTATUS active\nBUDGET run turns 0 of 80\n"))
    code, out = sb.kit("finish")
    r.eq("finish too early", (code, out), (3, "FINISH FAIL\n"))
finally:
    sb.close()

# ------------------------------------------------------------------ 3. repair succeeds
BAD = {"CLUE-04": {"PP-CLUE-04-2": "A chill ran down the corridor."}}
sb, _ = new(overrides=BAD)
try:
    plan = json.loads((sb.agent_dir / "S2" / "clue_plan.json").read_text())
    bible = json.loads((sb.agent_dir / "S1" / "bible.json").read_text())
    scenario.write_outputs(sb.agent_dir, "S5-S3-CLUE-04-R1", {"fill.json": scenario.make_fill("CLUE-04", plan, bible)})
    code, out = sb.kit("next", "--all")
    r.eq("repair run exit", code, 0)
    r.check("repair lines", "CHECK VL-01 FAIL PP-CLUE-04-2\nCHECK errors 1 warnings 0\nCHECK S3-CLUE-04 FAIL\nREPAIR S3-CLUE-04 round 1 READY\nAGENT S5-S3-CLUE-04-R1 started\n" in out
            and "CHECK S3-CLUE-04 PASS" in out and out.strip().endswith("All stages passed. Run finish."))
    r.eq("finish after repair", sb.kit("finish")[0], 0)
    rp = (sb.ws / "stages" / "S5-S3-CLUE-04-R1" / "prompt.md").read_text(encoding="utf-8")
    r.check("repair brief lists ID and requirement", "| VL-01 | PP-CLUE-04-2 | Remove signposting" in rp)
    r.check("repair brief has previous output", (sb.ws / "stages" / "S5-S3-CLUE-04-R1" / "inputs" / "previous" / "fill.json").is_file())
finally:
    sb.close()

# ------------------------------------------------------------------ 4. same check fails twice: abort
sb, _ = new(overrides=BAD)
try:
    plan = json.loads((sb.agent_dir / "S2" / "clue_plan.json").read_text())
    bible = json.loads((sb.agent_dir / "S1" / "bible.json").read_text())
    scenario.write_outputs(sb.agent_dir, "S5-S3-CLUE-04-R1", {"fill.json": scenario.make_fill("CLUE-04", plan, bible, BAD["CLUE-04"])})
    code, out = sb.kit("next", "--all")
    r.eq("abort repeat exit", code, 4)
    r.check("abort repeat lines", out.endswith("CHECK S3-CLUE-04 FAIL\nABORT S3-CLUE-04 same check failed in consecutive rounds\nABORT check VL-01\n"))
    r.eq("aborted run refuses next", sb.kit("next"), (4, "This run is not active.\n"))
finally:
    sb.close()

# ------------------------------------------------------------------ 5. different failures until the cap
sb, _ = new(overrides=BAD)
try:
    plan = json.loads((sb.agent_dir / "S2" / "clue_plan.json").read_text())
    bible = json.loads((sb.agent_dir / "S1" / "bible.json").read_text())
    scenario.write_outputs(sb.agent_dir, "S5-S3-CLUE-04-R1", {"fill.json": scenario.make_fill("CLUE-04", plan, bible, {"PP-CLUE-04-2": "I did it."})})
    scenario.write_outputs(sb.agent_dir, "S5-S3-CLUE-04-R2", {"fill.json": scenario.make_fill("CLUE-04", plan, bible, {"PP-CLUE-04-2": "word " * 200})})
    lim = copy.deepcopy(K.data("limits"))
    lim["turns"]["stage_caps"]["S5"] = 40
    lim["turns"]["run_cap"] = 200
    override_data("limits", lim)
    code, out = sb.kit("next", "--all")
    r.eq("abort cap exit", code, 4)
    r.check("abort cap lines", out.endswith("CHECK S3-CLUE-04 FAIL\nABORT S3-CLUE-04 repair rounds exhausted\nABORT check VL-12\n"))
finally:
    sb.close()

# ------------------------------------------------------------------ 6. budget stop
sb, _ = new(usage_json=False)
try:
    lim = copy.deepcopy(K.data("limits"))
    lim["turns"]["stage_caps"]["S3"] = 3
    override_data("limits", lim)
    code, out = sb.kit("next", "--all")
    r.eq("budget stop exit", code, 4)
    r.check("budget stop lines", out.endswith("BUDGET STOP S3 stage turn cap reached\nBUDGET S3 turns 3 of 3\nBUDGET run turns 25 of 80\n"))
    st = json.loads((sb.ws / "checkpoints" / "state.json").read_text())
    r.eq("budget stop leaves run resumable", (st["status"], st["current"]), ("active", None))
finally:
    sb.close()

# ------------------------------------------------------------------ 7. engine rule fails at S2, repair fixes it
sb, _ = new()
try:
    case = json.loads((sb.agent_dir / "S2" / "case.json").read_text())
    good = copy.deepcopy(case)
    case["clues"][0]["record_date"] = "FORCE-FAIL-FP02"
    scenario.write_outputs(sb.agent_dir, "S2", {"case.json": case})
    plan = json.loads((sb.agent_dir / "S2" / "clue_plan.json").read_text())
    skin = json.loads((sb.agent_dir / "S2" / "skin.json").read_text())
    scenario.write_outputs(sb.agent_dir, "S5-S2-R1", {"case.json": good, "clue_plan.json": plan, "skin.json": skin})
    code, out = sb.kit("next", "--all")
    r.eq("engine repair exit", code, 0)
    r.check("engine failure reported as ID and path", "CHECK FP-02 FAIL $.clues[0].record_date\n" in out and "REPAIR S2 round 1 READY" in out)
    rp = (sb.ws / "stages" / "S5-S2-R1" / "prompt.md").read_text(encoding="utf-8")
    r.check("engine rule text from rules file", "| FP-02 | $.clues[0].record_date | Fixture rule FP-02: nonsense requirement. |" in rp)
finally:
    sb.close()

# ------------------------------------------------------------------ 8. engine files change mid-run
sb, _ = new(mode_a=False)
try:
    sb.kit("next")
    (sb.ws / "stages" / "S1" / "bible.json").write_bytes((sb.agent_dir / "S1" / "bible.json").read_bytes())
    vocab = sb.root / "engine" / "schemas" / "vocabulary.json"
    vocab.write_text(vocab.read_text() + " ", encoding="utf-8")
    r.eq("drift aborts", sb.kit("check"), (4, "ABORT engine files changed since init\nABORT check KT-RN-02\n"))
finally:
    sb.close()

# ------------------------------------------------------------------ 9. setup errors
sb, _ = new()
try:
    r.eq("workspace reuse refused", sb.kit("init", "--root", str(sb.root)),
         (2, "A run already exists in this workspace. Use a new workspace folder.\n"))
    cfg = copy.deepcopy(K.data("kit_config"))
    cfg["agent"]["argv"] = []
    override_data("kit_config", cfg)
    code, out = sb.kit("next")
    r.eq("mode A without agent", (code, out.splitlines()[-1]), (2, "Mode A needs an agent command in kit_config.json (agent.argv)."))
finally:
    sb.close()
sb = Sandbox()
try:
    r.eq("no run yet", sb.kit("next"), (2, "No run found in this workspace. Run init first.\n"))
finally:
    sb.close()

# ------------------------------------------------------------------ 10. optional craft review (S6)
sb, _ = new(review=True)
try:
    scenario.write_outputs(sb.agent_dir, "S6", {"review.json": {"scores": {f"RUB-{i}": 2 for i in range(11, 21)}, "flags": ["FM-05"]}})
    code, out = sb.kit("next", "--all")
    r.eq("review run exit", code, 0)
    r.check("review prints scores and flags only", "REVIEW RUB-11 2\n" in out and "REVIEW FLAG FM-05\n" in out)
finally:
    sb.close()
sb, _ = new(review=True)
try:
    scenario.write_outputs(sb.agent_dir, "S6", {"review.json": {"scores": {"RUB-11": 2}, "flags": [], "note": CANARY}})
    scenario.write_outputs(sb.agent_dir, "S5-S6-R1", {"review.json": {"scores": {"RUB-11": 2}, "flags": [], "note": CANARY}})
    code, out = sb.kit("next", "--all")
    r.check("review with text refused", code == 4 and "CHECK KT-RV-01 FAIL $" in out and CANARY not in out)
finally:
    sb.close()

sys.exit(r.finish())
