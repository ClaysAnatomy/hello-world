"""End-to-end tests for kit_run with the fake engine and fake agent.

Covers Mode A and Mode B, stage folders outside the workspace that close after
acceptance, repair success, abort on repeat, abort at the cap, budget stop,
pause and resume on a usage limit, engine-rule failure and repair, placeholder
tolerance, engine drift, setup errors, the optional review, the cross-family
blind audit, estimates, and canary tests proving planted strings never reach
the screen, the logs, the ledger, the project tree, or the folders that must
not see them.

Run: python test_kit_run.py            (compare with the golden transcript)
     python test_kit_run.py --regold   (rewrite the golden transcript)
"""
import copy
import json
import re
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
    extra = ["--root", str(sb.root), "--seed", str(seed), "--stage-root", str(sb.tmp / "stages_root")]
    extra += ["--review"] if review else []
    code, out = sb.kit("init", *extra)
    assert code == 0, out
    scenario.stage_all(sb.agent_dir, sb.seeds(), overrides)
    return sb, out


def state(sb):
    return json.loads((sb.ws / "checkpoints" / "state.json").read_text(encoding="utf-8"))


def norm(text, sb):
    """Replace this sandbox's temp paths so the golden transcript is stable."""
    return text.replace(str(sb.tmp / "stages_root"), "<STAGE_ROOT>")


# ------------------------------------------------------------------ 1. happy path, Mode A
sb, init_out = new()
try:
    sr = Path(state(sb)["stage_root"])
    r.check("stage root outside workspace", sb.ws not in sr.parents and sr != sb.ws)
    code, run_out = sb.kit("next", "--all")
    r.eq("mode A next exit", code, 0)
    r.eq("no stage folder inside the workspace", (sb.ws / "stages").exists(), False)
    r.eq("accepted stage folders closed", sorted(p.name for p in sr.iterdir()), [".mm_kit_stage_root"])
    code, fin_out = sb.kit("finish")
    r.eq("finish exit", code, 0)
    r.eq("stage root removed at finish", sr.exists(), False)
    transcript = norm(init_out + "--- next --all\n" + run_out + "--- finish\n" + fin_out, sb)
    if "--regold" in sys.argv:
        GOLDEN.write_text(transcript, encoding="utf-8")
    r.eq("golden transcript", transcript, GOLDEN.read_text(encoding="utf-8"))
    st = state(sb)
    r.eq("status finished", st["status"], "finished")
    r.eq("turns from usage report", st["budget"]["turns"]["S3"], 20)
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
    units = sb.ws / "checkpoints" / "units"
    blind = [p for d in units.iterdir() if d.name.startswith(("S3-", "S4")) for p in files_under(d) if file_contains(p, KEY_CANARY)]
    r.eq("answer key never in S3 or S4 briefs", blind, [])
    s4 = (units / "S4" / "prompt.md").read_text(encoding="utf-8")
    r.check("S4 brief hides correctness", '"correct"' not in s4)
    prompts = list(units.rglob("prompt.md"))
    r.check("all prompts rendered", len(prompts) >= 13 and not any("{{" in p.read_text(encoding="utf-8") for p in prompts))
    s3 = (units / "S3-CLUE-04" / "prompt.md").read_text(encoding="utf-8")
    r.check("S3 brief has the neighbour index", "## The other papers in this archive" in s3 and "dated 2026-03-04, by" in s3)
    r.check("neighbour index carries no facts", "FACT-0" not in s3.split("## The other papers in this archive")[1].split("## Fields")[0])
    calls = sb.calls()
    r.eq("agent saw no secret variables", sorted({v for c in calls for v in c["secret_vars"]}), [])
    r.check("prompt sent on stdin", all(c["stdin_chars"] > 500 for c in calls))
    r.eq("max turns passed to agent", calls[0]["argv"], ["12"])
    claims = json.loads((sb.ws / "claims.json").read_text(encoding="utf-8"))["claims"]
    r.check("claims are paths and IDs", all(c["path"].startswith("$.") and all(f.startswith("FACT-") for f in c["facts"]) for c in claims))
    case = json.loads((sb.ws / "case.json").read_text(encoding="utf-8"))
    r.check("no placeholder left", not any(s.startswith("PP-") for s in K.string_leaves(case)))
    man_path = sb.ws / "media_manifest.json"
    r.check("media manifest written", man_path.is_file())
    man = json.loads(man_path.read_text(encoding="utf-8"))
    r.check("manifest holds no answer key or facts", not file_contains(man_path, KEY_CANARY) and "FACT-" not in man_path.read_text(encoding="utf-8"))
    r.check("media registry stays sealed in checkpoints", (sb.ws / "checkpoints" / "media_registry.json").is_file())
    rep = next(i for i in man["items"] if i["id"] == "CLUE-01")
    body = case["clues"][0]["raw_observation_text"]
    r.check("every value on the report form is in its text", all(x["text"] in body for x in rep["regions"] if x["role"] == "registry"))
    s3m = (units / "S3-CLUE-01" / "prompt.md").read_text(encoding="utf-8")
    r.check("S3 brief lists the printed values", all(x["text"] in s3m for x in rep["regions"] if x["role"] == "registry"))
    r.check("plain S3 brief says plain text", "plain text" in (units / "S3-CLUE-04" / "prompt.md").read_text(encoding="utf-8"))
finally:
    sb.close()

# ------------------------------------------------------------------ 2. Mode B, and live stage-folder isolation
sb, _ = new(mode_a=False)
try:
    sr = Path(state(sb)["stage_root"])
    code, out = sb.kit("next")
    r.eq("mode B next", (code, norm(out, sb)), (3, "NEXT S1 READY\nPROMPT <STAGE_ROOT>/S1/prompt.md\n"))
    code, out = sb.kit("next")
    r.eq("mode B waiting", (code, out), (3, "Stage S1 is waiting for a check. Run check.\n"))
    scenario.place_s1(sb.agent_dir, sr / "S1")
    code, out = sb.kit("check")
    r.eq("mode B check", (code, out), (0, "CHECK errors 0 warnings 0\nCHECK S1 PASS\n"))
    r.eq("S1 folder closed after acceptance", (sr / "S1").exists(), False)
    code, out = sb.kit("check")
    r.eq("nothing to check", (code, out), (3, "No stage is waiting for a check. Run next first.\n"))
    code, out = sb.kit("status")
    r.eq("status", (code, out), (0, "STATUS units done 1 of 2\nSTATUS active\nBUDGET run turns 0 of 80\n"))
    r.eq("finish too early", sb.kit("finish"), (3, "FINISH FAIL\n"))
    sb.kit("next")
    for n in ("clue_plan.json", "case.json", "skin.json"):
        (sr / "S2" / n).write_bytes((sb.agent_dir / "S2" / n).read_bytes())
    r.eq("mode B S2 check", sb.kit("check")[0], 0)
    sb.kit("next")
    live = sorted(p.name for p in sr.iterdir())
    r.eq("only the current unit exists on disk", live, [".mm_kit_stage_root", "S3-CLUE-01"])
    r.eq("S3 folder holds only the fill schema", sorted(p.name for p in (sr / "S3-CLUE-01" / "inputs").iterdir()), ["fill.schema.json"])
    r.check("S3 folder holds no answer key", not any(file_contains(p, KEY_CANARY) for p in files_under(sr)))
finally:
    sb.close()

# ------------------------------------------------------------------ 3. repair succeeds
BAD = {"CLUE-04": {"PP-CLUE-04-2": "A chill ran down the corridor."}}
sb, _ = new(overrides=BAD)
try:
    plan = json.loads((sb.agent_dir / "S2" / "clue_plan.json").read_text())
    bible = scenario.load_bible(sb.agent_dir)
    scenario.write_outputs(sb.agent_dir, "S5-S3-CLUE-04-R1", {"fill.json": scenario.make_fill("CLUE-04", plan, bible)})
    code, out = sb.kit("next", "--all")
    r.eq("repair run exit", code, 0)
    r.check("repair lines", "CHECK VL-01 FAIL PP-CLUE-04-2\nCHECK errors 1 warnings 0\nCHECK S3-CLUE-04 FAIL\nREPAIR S3-CLUE-04 round 1 READY\nAGENT S5-S3-CLUE-04-R1 started\n" in out
            and "CHECK S3-CLUE-04 PASS" in out and out.strip().endswith("All stages passed. Run finish."))
    r.eq("finish after repair", sb.kit("finish")[0], 0)
    rp = (sb.ws / "checkpoints" / "units" / "S3-CLUE-04" / "prompt.md").read_text(encoding="utf-8")
    r.check("repair brief lists ID and requirement", "| VL-01 | PP-CLUE-04-2 | Remove signposting" in rp)
finally:
    sb.close()

# ------------------------------------------------------------------ 4. same check fails twice: abort
sb, _ = new(overrides=BAD)
try:
    plan = json.loads((sb.agent_dir / "S2" / "clue_plan.json").read_text())
    bible = scenario.load_bible(sb.agent_dir)
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
    bible = scenario.load_bible(sb.agent_dir)
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
    r.check("budget stop lines", out.endswith("BUDGET STOP S3 stage turn cap reached\nBUDGET S3 turns 3 of 3\nBUDGET run turns 31 of 80\n"))
    st = state(sb)
    r.eq("budget stop leaves run resumable", (st["status"], st["current"]), ("active", None))
finally:
    sb.close()

# ------------------------------------------------------------------ 7. usage limit pauses, next resumes
sb, _ = new()
try:
    (sb.agent_dir / "_pause_S3-CLUE-02").write_text("x")
    code, out = sb.kit("next", "--all")
    r.eq("pause exit", code, 5)
    r.check("pause lines", out.endswith("AGENT S3-CLUE-02 paused: usage limit. Run next again later to resume.\nBUDGET S3 turns 3 of 36\nBUDGET run turns 7 of 80\n"))
    st = state(sb)
    r.eq("paused state kept", (st["status"], st["current"]["unit"], st["failure"]), ("paused", "S3-CLUE-02", None))
    r.eq("status shows paused", sb.kit("status")[1].splitlines()[1], "STATUS paused")
    code, out = sb.kit("next", "--all")
    r.eq("resume completes", code, 0)
    r.check("resume restarts the same unit and uses no repair", out.startswith("AGENT S3-CLUE-02 started") and "REPAIR" not in out)
finally:
    sb.close()

# ------------------------------------------------------------------ 8. engine rules: tolerated at S2, enforced later, repaired when real
sb, _ = new()
try:
    lim = copy.deepcopy(K.data("limits"))
    lim["tolerated_engine_rules"]["S2"] = []
    override_data("limits", lim)
    code, out = sb.kit("next")
    code, out = sb.kit("next")
    r.check("prose rule fails on placeholders without tolerance", "CHECK FP-03 FAIL $.clues[0].raw_observation_text" in out and "CHECK S2 FAIL" in out)
finally:
    sb.close()
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
    rp = (sb.ws / "checkpoints" / "units" / "S2" / "prompt.md").read_text(encoding="utf-8")
    r.check("engine rule text from rules file", "| FP-02 | $.clues[0].record_date | Fixture rule FP-02: nonsense requirement. |" in rp)
finally:
    sb.close()

# ------------------------------------------------------------------ 9. gate failure re-opens a closed unit
sb, _ = new()
try:
    plan = json.loads((sb.agent_dir / "S2" / "clue_plan.json").read_text())
    bible = scenario.load_bible(sb.agent_dir)
    shared = "the boiler in the east store was cold again by the second bell and nobody had signed the book"
    for o in ("CLUE-02", "CLUE-03"):
        f = scenario.make_fill(o, plan, bible)
        f["fills"][f"PP-{o}-2"] += " " + shared
        scenario.write_outputs(sb.agent_dir, f"S3-{o}", {"fill.json": f})
    scenario.write_outputs(sb.agent_dir, "S5-S3-CLUE-03-R1", {"fill.json": scenario.make_fill("CLUE-03", plan, bible)})
    code, out = sb.kit("next", "--all")
    r.eq("gate repair exit", code, 0)
    r.check("gate blames the later document", "CHECK VL-09 FAIL CLUE-03\n" in out and "GATE S3 FAIL" in out and "REPAIR S3-CLUE-03 round 1 READY" in out and "GATE S3 PASS" in out)
finally:
    sb.close()

# ------------------------------------------------------------------ 10. engine files change mid-run
sb, _ = new(mode_a=False)
try:
    sb.kit("next")
    sr = Path(state(sb)["stage_root"])
    scenario.place_s1(sb.agent_dir, sr / "S1")
    vocab = sb.root / "engine" / "schemas" / "vocabulary.json"
    vocab.write_text(vocab.read_text() + " ", encoding="utf-8")
    r.eq("drift aborts", sb.kit("check"), (4, "ABORT engine files changed since init\nABORT check KT-RN-02\n"))
finally:
    sb.close()

# ------------------------------------------------------------------ 11. setup errors
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
    code, out = sb.kit("init", "--root", str(sb.root), "--stage-root", str(sb.ws / "inside"))
    r.eq("stage root inside workspace refused", (code, out.splitlines()[-1]), (2, "The stage folder must not be inside the workspace. Choose another --stage-root."))
finally:
    sb.close()

# ------------------------------------------------------------------ 12. optional craft review (S6)
sb, _ = new(review=True)
try:
    scenario.write_outputs(sb.agent_dir, "S6", {"review.json": {"scores": {**{f"RUB-{i}": 2 for i in range(11, 21)}, "RUB-29": 2}, "flags": ["FM-02"]}})
    code, out = sb.kit("next", "--all")
    r.eq("review run exit", code, 0)
    r.check("review prints scores and flags only", "REVIEW RUB-11 2\n" in out and "REVIEW FLAG FM-02\n" in out)
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


# ------------------------------------------------------------------ 13. cross-family blind audit
def bundle_for(sb):
    case = json.loads((sb.ws / "case.json").read_text(encoding="utf-8"))
    path = sb.tmp / "player_bundle.json"
    path.write_text(json.dumps({"questions": case["questions"], "clues": case["clues"]}), encoding="utf-8")
    return path


def answers(bible, mode, right=True, cite=True, confidence=0.9):
    plan_gold = {"Q01": ["CLUE-02", "CLUE-04"], "Q02": ["CLUE-02", "CLUE-07"]}
    v = {}
    for q in bible["questions"]:
        good = next(o["id"] for o in q["options"] if o["correct"])
        bad = next(o["id"] for o in q["options"] if not o["correct"])
        v[q["id"]] = {"selected_opt": good if right else bad, "confidence": confidence,
                      "cited": (plan_gold[q["id"]] if cite else ["CLUE-01"]) if mode == "SOLVE" else []}
    return {"mode": mode, "verdict": v, "stage_1_extracted_clues": [{"note": CANARY}]}


sb, _ = new()
try:
    sb.kit("next", "--all")
    r.eq("audit before finish refused", sb.kit("audit", "--bundle", "x.json"), (3, "The audit runs only after finish passes.\n"))
    sb.kit("finish")
    bible = json.loads((sb.ws / "checkpoints" / "bible.json").read_text(encoding="utf-8"))
    scenario.write_outputs(sb.agent_dir, "S7-SOLVE", {"answers.json": answers(bible, "SOLVE")})
    scenario.write_outputs(sb.agent_dir, "S7-SHORTCUT", {"answers.json": answers(bible, "SHORTCUT", right=False, confidence=0.4)})
    code, out = sb.kit("audit", "--bundle", str(bundle_for(sb)))
    r.eq("audit pass exit", code, 0)
    r.check("audit lines", "AUDIT Q01 AU-01 PASS\nAUDIT Q01 cite precision 1.00 coverage 1.00 jaccard 0.50\nAUDIT Q01 AU-02 PASS\nAUDIT Q01 AU-03 PASS\n" in out and out.endswith("AUDIT PASS\n"))
    r.check("audit never prints the solver's text", CANARY not in out)
    report = json.loads((sb.ws / "checkpoints" / "audit" / "report.json").read_text(encoding="utf-8"))
    r.check("audit report holds numbers and IDs only", CANARY not in json.dumps(report) and report["pass"] is True)
    calls = [c["unit"] for c in sb.calls()]
    r.check("both audit modes ran", "S7-SHORTCUT" in calls and "S7-SOLVE" in calls)
    shortcut_inputs = json.loads((sb.ws / "checkpoints" / "audit" / "SHORTCUT.json").read_text())
    r.eq("shortcut answers stored sealed", shortcut_inputs["mode"], "SHORTCUT")
finally:
    sb.close()
sb, _ = new()
try:
    sb.kit("next", "--all")
    sb.kit("finish")
    bible = json.loads((sb.ws / "checkpoints" / "bible.json").read_text(encoding="utf-8"))
    scenario.write_outputs(sb.agent_dir, "S7-SOLVE", {"answers.json": answers(bible, "SOLVE", cite=False)})
    scenario.write_outputs(sb.agent_dir, "S7-SHORTCUT", {"answers.json": answers(bible, "SHORTCUT", right=True, confidence=0.9)})
    code, out = sb.kit("audit", "--bundle", str(bundle_for(sb)))
    r.check("audit catches bad citations and a giveaway", code == 1 and "AUDIT Q01 AU-02 FAIL" in out and "AUDIT Q01 AU-03 FAIL" in out and out.endswith("AUDIT FAIL\n"))
    cfg = copy.deepcopy(K.data("kit_config"))
    cfg["audit_agent"]["family"] = cfg["agent"]["family"]
    override_data("kit_config", cfg)
    r.eq("same family refused", sb.kit("audit", "--bundle", str(bundle_for(sb)))[0], 2)
    sr = Path(state(sb)["stage_root"])
    shortcut_dir_inputs = [p.name for p in (sr / "S7-SHORTCUT" / "inputs").iterdir()] if (sr / "S7-SHORTCUT").exists() else []
    r.check("shortcut probe never sees records", "player_bundle.json" not in shortcut_dir_inputs)
finally:
    sb.close()

# ------------------------------------------------------------------ 14. estimate
sb = Sandbox()
try:
    r.eq("estimate 10 documents", sb.run("estimate", "--documents", "10"),
         (0, "ESTIMATE documents 10 invocations 14 turns at cap 72 of 80\nESTIMATE S3 turns at cap 30 of 36\nESTIMATE fits the caps\n"))
    r.eq("estimate 15 documents", sb.run("estimate", "--documents", "15")[1].splitlines()[-1], "ESTIMATE exceeds a cap")
    r.eq("12 documents and 1 repair fit", sb.run("estimate", "--documents", "12")[1].splitlines()[-1], "ESTIMATE fits the caps")
    r.eq("12 documents and 2 repairs do not", sb.run("estimate", "--documents", "12", "--repairs", "2")[1].splitlines()[-1],
         "ESTIMATE exceeds a cap")
finally:
    sb.close()

# ------------------------------------------------------------------ 15. the first real run: a bible part cut off mid-write
FACTS = "bible_parts/4_facts.json"
sb, _ = new()
try:
    bible = scenario.load_bible(sb.agent_dir)
    full = (sb.agent_dir / "S1" / FACTS).read_text(encoding="utf-8")
    (sb.agent_dir / "S1" / FACTS).unlink()
    cut = full[: full.rindex("},") + 2]  # ends with a comma, like the real file did
    raw = sb.agent_dir / "_raw_S1" / FACTS
    raw.parent.mkdir(parents=True)
    raw.write_text(cut + f"  \"note\": \"{CANARY}\",", encoding="utf-8")
    (sb.agent_dir / "_result_S1").write_text("error_max_turns", encoding="utf-8")
    scenario.write_outputs(sb.agent_dir, "S5-S1-R1", {FACTS: {"facts": bible["facts"]}})
    code, out = sb.kit("next", "--all")
    lines = cut.count("\n") + 1
    r.eq("cut-off run completes after one repair", code, 0)
    r.check("cut-off part named with its line", f"CHECK KT-IO-02 FAIL {FACTS} at line " in out)
    r.check("no bare dollar for a broken file", "CHECK KT-IO-02 FAIL $" not in out and "KT-BI-01" not in out)
    r.check("agent result word shown", "AGENT S1 exit 1\nAGENT S1 result error_max_turns\nAGENT S1 ran " in out)
    r.check("cut-off canary never printed", CANARY not in out)
    calls = sb.calls()
    rep = next(c for c in calls if c["unit"] == "S5-S1-R1")
    r.eq("bible repair gets its own turn cap", rep["argv"], ["8"])
    log = json.loads((sb.ws / "checkpoints" / "agent_log.json").read_text(encoding="utf-8"))
    r.eq("agent log keeps the result word", [e.get("result") for e in log[:2]], ["error_max_turns", "success"])
    r.check("agent log holds no text", not file_contains(sb.ws / "checkpoints" / "agent_log.json", CANARY))
    r.check("agent log keys are numbers and one word",
            all(set(e) <= {"unit", "exit", "result", "turns", "seconds", "denials", "cost_usd"} for e in log))
    joined = json.loads((sb.ws / "checkpoints" / "bible.json").read_text(encoding="utf-8"))
    r.eq("joined bible equals the parts", joined, bible)
finally:
    sb.close()

# the repair brief: pre-seeded parts, the broken one marked, the turn budget stated
sb, _ = new(mode_a=False)
try:
    sb.kit("next")
    sr = Path(state(sb)["stage_root"])
    scenario.place_s1(sb.agent_dir, sr / "S1")
    t = (sr / "S1" / FACTS).read_text(encoding="utf-8")
    (sr / "S1" / FACTS).write_text(t[: t.rindex("},") + 2], encoding="utf-8")
    code, out = sb.kit("check")
    r.check("mode B cut-off check", code == 1 and f"CHECK KT-IO-02 FAIL {FACTS} at line" in out)
    s1p = (sr / "S1" / "prompt.md").read_text(encoding="utf-8")
    r.check("S1 brief lists five parts and the turn budget",
            all(pp["file"] in s1p for pp in K.data("stage_plan")["bible_parts"]) and "at most 12 turns" in s1p
            and "never append" in s1p and "KT-IO-02" in s1p)
    code, out = sb.kit("repair")
    rdir = sr / "S5-S1-R1"
    r.check("other parts already in place for the repair", (rdir / "bible_parts" / "1_premise.json").is_file()
            and (rdir / "bible_parts" / "5_reveal.json").is_file())
    rp = (rdir / "prompt.md").read_text(encoding="utf-8")
    r.check("repair brief marks the broken part", f"`{FACTS}`: your previous output, already in place; it is broken" in rp)
    r.check("repair brief gives file and line", f"| KT-IO-02 | {FACTS}, line " in rp and "at most 8 turns" in rp)
    (rdir / FACTS).write_bytes((sb.agent_dir / "S1" / FACTS).read_bytes())
    r.eq("repair of one part passes", sb.kit("check")[0], 0)
finally:
    sb.close()

# missing part, duplicate field, BOM, schema field, single-file fallback
def s1_check(prepare):
    sb, _ = new(mode_a=False)
    try:
        sb.kit("next")
        sr = Path(state(sb)["stage_root"])
        scenario.place_s1(sb.agent_dir, sr / "S1")
        prepare(sr / "S1", sb)
        return sb.kit("check")
    finally:
        sb.close()

code, out = s1_check(lambda d, sb: (d / "bible_parts" / "3_truth.json").unlink())
r.eq("missing part", (code, out.splitlines()[0]), (1, "CHECK KT-IO-01 FAIL bible_parts/3_truth.json"))

def dup(d, sb):
    p = d / "bible_parts" / "5_reveal.json"
    o = json.loads(p.read_text(encoding="utf-8"))
    o["facts"] = []
    p.write_text(json.dumps(o), encoding="utf-8")
code, out = s1_check(dup)
r.eq("field in two parts", (code, out.splitlines()[0]), (1, "CHECK KT-IO-03 FAIL bible_parts/5_reveal.json"))

def bom(d, sb):
    p = d / "bible_parts" / "2_people.json"
    p.write_bytes(b"\xef\xbb\xbf" + p.read_bytes())
r.eq("byte-order mark accepted", s1_check(bom)[0], 0)

def drop_cover(d, sb):
    p = d / "bible_parts" / "3_truth.json"
    o = json.loads(p.read_text(encoding="utf-8"))
    o.pop("cover")
    p.write_text(json.dumps(o), encoding="utf-8")
code, out = s1_check(drop_cover)
r.eq("missing field named", (code, out.splitlines()[0]), (1, "CHECK KT-BI-01 FAIL $.cover"))

def single(d, sb):
    import shutil
    shutil.rmtree(d / "bible_parts")
    (d / "bible.json").write_text(json.dumps(scenario.load_bible(sb.agent_dir)), encoding="utf-8")
r.eq("single bible.json still accepted", s1_check(single)[0], 0)

def extra(d, sb):
    p = d / "bible_parts" / "1_premise.json"
    o = json.loads(p.read_text(encoding="utf-8"))
    o[CANARY.replace(" ", "_")] = 1
    p.write_text(json.dumps(o), encoding="utf-8")
code, out = s1_check(extra)
r.check("extra field withheld, not printed", code == 1 and out.splitlines()[0] == "CHECK KT-BI-01 FAIL WITHHELD" and CANARY.split()[0] not in out)

# ------------------------------------------------------------------ 16. timeout and permission denials
sb, _ = new()
try:
    lim = copy.deepcopy(K.data("limits"))
    lim["timeouts"]["stage_minutes"] = 0
    override_data("limits", lim)
    code, out = sb.kit("next", "--all")
    r.check("timeout says minutes and unknown cost",
            "AGENT S1 timed out after 0 minutes\nAGENT S1 reported no turns or cost:" in out)
    st = sb.kit("status")[1]
    r.check("status counts the unknown cost", "BUDGET cost not reported for 2 agent run(s)" in st)
    r.check("aborted status does not offer a repair", "STATUS aborted" in st and "Run repair" not in st)
finally:
    sb.close()

sb, _ = new()
try:
    (sb.agent_dir / "_result_S1").write_text("denied", encoding="utf-8")
    code, out = sb.kit("next", "--all")
    r.check("denials counted, never shown", "AGENT S1 permission denials 1" in out and CANARY not in out)
finally:
    sb.close()

sys.exit(r.finish())
