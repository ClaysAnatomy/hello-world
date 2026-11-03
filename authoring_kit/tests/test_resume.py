"""Tests for kit v4.2: work is never paid for twice. Run: python test_resume.py

Saved attempts, recovery after an interruption, resume after an abort or a stop,
the split S2, inline inputs, cleanup and preflight.
"""
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_test_util import K, Report, Sandbox, file_contains, files_under, override_data, reset_data  # noqa: E402
import scenario  # noqa: E402
from scenario import CANARY, KEY_CANARY  # noqa: E402
import kit_run  # noqa: E402

r = Report("test_resume")


def new(**kw):
    sb = Sandbox(mode_a=True, usage_json=True)
    code, out = sb.kit("init", "--root", str(sb.root), "--seed", "7", "--stage-root", str(sb.tmp / "stages_root"))
    assert code == 0, out
    scenario.stage_all(sb.agent_dir, sb.seeds(), kw.get("overrides"))
    return sb


def state(sb):
    return json.loads((sb.ws / "checkpoints" / "state.json").read_text(encoding="utf-8"))


def put_state(sb, st):
    (sb.ws / "checkpoints" / "state.json").write_text(json.dumps(st), encoding="utf-8")


def agent_units(sb):
    return [c.get("unit") for c in sb.calls()]


# ------------------------------------------------------------------ 1. split S2 and inline inputs
sb = new()
try:
    code, out = sb.kit("next", "--all")
    r.eq("full run with S2A and S2B", code, 0)
    r.check("both halves ran in order", out.index("CHECK S2A PASS") < out.index("AGENT S2B started") < out.index("CHECK S2B PASS"))
    units = sb.ws / "checkpoints" / "units"
    s2a = (units / "S2A" / "prompt.md").read_text(encoding="utf-8")
    s2b = (units / "S2B" / "prompt.md").read_text(encoding="utf-8")
    r.check("S2A carries its inputs inline", "## Inputs, in full" in s2a and "`inputs/bible.json`" in s2a)
    r.check("S2A gets no engine files", "fixture_case.json" not in s2a and "engine_schemas/" not in s2a)
    r.check("S2B gets the plan and engine files inline", "`inputs/clue_plan.json`" in s2b and "`inputs/fixture_case.json`" in s2b)
    r.check("S2B gets no forms or techniques tables", "## Document forms" not in s2b and "## Techniques" not in s2b)
    r.check("inline JSON is minified", '{"kit_version":' in s2a)
    r.check("turn budget says not to read files", "do not read any file" in s2a)
    s3 = (units / "S3-CLUE-01" / "prompt.md").read_text(encoding="utf-8")
    r.check("S3 inline holds no answer key", KEY_CANARY not in s3)
    r.check("every output saved to attempts", all((sb.ws / "checkpoints" / "attempts" / u).is_dir() for u in ("S1", "S2A", "S2B", "S3-CLUE-01", "S4")))
    r.eq("finish", sb.kit("finish")[0], 0)
    r.check("attempts stay inside the sealed workspace", not any(file_contains(p, KEY_CANARY) for p in files_under(sb.root)))
    code, est = sb.kit("estimate", "--documents", "10")
    r.check("estimate uses the measured cost per turn", "ESTIMATE cost about" in est and "WITHHELD" not in est)
finally:
    sb.close()

# ------------------------------------------------------------------ 2. an interrupted unit with outputs is checked, never re-run
sb = new()
try:
    sb.kit("next")  # S1
    st = state(sb)
    cur = {"unit": "S2A", "stage": "S2A", "owner": None, "target": "S2A", "round": 0}
    st["current"] = cur
    put_state(sb, st)
    saved = sb.ws / "checkpoints" / "attempts" / "S2A"
    saved.mkdir(parents=True)
    shutil.copy(sb.agent_dir / "S2A" / "clue_plan.json", saved / "clue_plan.json")
    before = len(sb.calls())
    code, out = sb.kit("next")
    r.eq("recovered unit passes", code, 0)
    r.check("recovered unit was checked, not re-run", "CHECK S2A PASS" in out and "AGENT S2A started" not in out)
    r.eq("no agent call for the recovered unit", len(sb.calls()), before)
    # nothing written: the unit is simply run
    st = state(sb)
    st["current"] = {"unit": "S2B", "stage": "S2B", "owner": None, "target": "S2B", "round": 0}
    put_state(sb, st)
    code, out = sb.kit("next")
    r.check("unit with no saved work runs normally", "AGENT S2B started" in out and "CHECK S2B PASS" in out)
finally:
    sb.close()

# ------------------------------------------------------------------ 3. resume after an abort keeps accepted work
BAD = {"CLUE-04": {"PP-CLUE-04-2": "A chill ran down the corridor."}}
sb = new(overrides=BAD)
try:
    plan = json.loads((sb.agent_dir / "S2A" / "clue_plan.json").read_text())
    bible = scenario.load_bible(sb.agent_dir)
    scenario.write_outputs(sb.agent_dir, "S5-S3-CLUE-04-R1", {"fill.json": scenario.make_fill("CLUE-04", plan, bible, BAD["CLUE-04"])})
    code, out = sb.kit("next", "--all")
    r.eq("aborts on the repeated check", code, 4)
    r.check("abort removes the stage folders", not (sb.tmp / "stages_root").exists())
    r.check("abort keeps the failed attempt", (sb.ws / "checkpoints" / "attempts" / "S5-S3-CLUE-04-R1" / "fill.json").is_file())
    spent = round(sum(state(sb)["budget"]["cost_usd"].values()), 2)
    done_before = list(state(sb)["done"])
    # a fixed repair is now available
    scenario.write_outputs(sb.agent_dir, "S5-S3-CLUE-04-R1", {"fill.json": scenario.make_fill("CLUE-04", plan, bible)})
    code, out = sb.kit("resume", "--stage-root", str(sb.tmp / "stages_root2"))
    r.eq("resume exit", code, 0)
    r.eq("resume line", out.splitlines()[0], f"RESUME from S3-CLUE-04: kept {len(done_before)} accepted units; previous spend {spent:.2f} dollars recorded")
    st = state(sb)
    r.eq("resumed run is active with fresh rounds", (st["status"], st["failure"]["round"], st["failure"]["history"]), ("active", 0, []))
    r.eq("new pass, old spend kept", (st["budget"]["turns"], len(st["budget"]["passes"])), ({}, 1))
    before = agent_units(sb)
    code, out = sb.kit("next", "--all")
    r.eq("resumed run completes", code, 0)
    r.check("accepted units were not re-run", "AGENT S1 started" not in out and "AGENT S2A started" not in out and "AGENT S3-CLUE-01 started" not in out)
    r.check("it continued from the repair", out.startswith("REPAIR S3-CLUE-04 round 1 READY"))
    r.eq("finish after resume", sb.kit("finish")[0], 0)
    r.check("nothing sealed on screen", CANARY not in out and KEY_CANARY not in out)
    r.eq("resume a finished run", sb.kit("resume"), (0, "RESUME nothing to resume: this run is finished.\n"))
finally:
    sb.close()

# ------------------------------------------------------------------ 4. resume after a budget stop
sb = new()
try:
    lim = K.data("limits")
    lim = json.loads(json.dumps(lim))
    lim["turns"]["stage_caps"]["S3"] = 3
    override_data("limits", lim)
    code, out = sb.kit("next", "--all")
    r.eq("budget stop", code, 4)
    lim["turns"]["stage_caps"]["S3"] = 60
    override_data("limits", lim)
    code, out = sb.kit("resume")
    r.check("resume after a stop keeps the stage root", out.splitlines()[1] == f"STAGES {(sb.tmp / 'stages_root').resolve()}")
    code, out = sb.kit("next", "--all")
    r.eq("completes after the stop", code, 0)
    r.check("S1 and S2 not paid for twice", "AGENT S1 started" not in out and "AGENT S2A started" not in out and "AGENT S2B started" not in out)
finally:
    sb.close()

# ------------------------------------------------------------------ 5. a run from before the split resumes at S2A
sb = new()
try:
    sb.kit("next")  # S1
    st = state(sb)
    st["failure"] = {"unit": "S2", "findings": [{"id": "KT-PL-01", "path": "$", "sev": "ERROR"}], "round": 0,
                     "history": [["KT-PL-01"]], "outputs_dir": str(sb.tmp / "gone")}
    st["status"] = "aborted"
    put_state(sb, st)
    code, out = sb.kit("resume", "--stage-root", str(sb.tmp / "stages_root3"))
    r.eq("old S2 failure resumes at S2A", out.splitlines()[0], "RESUME from S2A: kept 1 accepted units; previous spend 0.01 dollars recorded")
    code, out = sb.kit("next", "--all")
    r.check("then runs the split stages", code == 0 and "AGENT S1 started" not in out and "CHECK S2A PASS" in out and "CHECK S2B PASS" in out)
finally:
    sb.close()

# ------------------------------------------------------------------ 6. cleanup removes only old marked stage roots, unopened
tmp = Path(tempfile.mkdtemp(prefix="kit_clean_"))
old_tempdir = tempfile.tempdir
try:
    tempfile.tempdir = str(tmp)
    old = tmp / "mm_kit_stages_old"
    (old / "S2A").mkdir(parents=True)
    (old / kit_run.Run.MARKER).write_text("x")
    (old / "S2A" / "bible.json").write_text("{}")
    past = time.time() - 48 * 3600
    os.utime(old, (past, past))
    fresh = tmp / "mm_kit_stages_new"
    fresh.mkdir()
    (fresh / kit_run.Run.MARKER).write_text("x")
    unmarked = tmp / "mm_kit_stages_other"
    unmarked.mkdir()
    os.utime(unmarked, (past, past))
    import io
    buf = io.StringIO()
    code = kit_run.Run.cleanup(12, out=K.Out(stream=buf))
    r.eq("cleanup output", buf.getvalue(), "CLEANUP removed 1 stage folders, kept 1\n")
    r.check("old marked root removed", not old.exists())
    r.check("recent root kept", fresh.exists())
    r.check("unmarked folder never touched", unmarked.exists())
finally:
    tempfile.tempdir = old_tempdir
    shutil.rmtree(tmp, ignore_errors=True)

# ------------------------------------------------------------------ 7. preflight
sb = Sandbox()
try:
    code, out = sb.run("preflight", "--root", str(sb.root))
    r.check("preflight prints IDs and verdicts only", "WITHHELD" not in out and all(l.startswith("PREFLIGHT") for l in out.splitlines()))
    r.check("fake agent has no --restricted", "PREFLIGHT PF-02 FAIL" in out and code == 1)
    cfg = json.loads(json.dumps(K.data("kit_config")))
    cfg["agent"]["argv"] = ["claude", "-p", "--restricted", "--settings", str(sb.root / "missing.json"), "--output-format", "json"]
    cfg["agent"]["usage_from_stdout_json"] = True
    override_data("kit_config", cfg)
    code, out = sb.run("preflight", "--root", str(sb.root))
    r.check("missing settings file fails", "PREFLIGHT PF-02 PASS" in out and "PREFLIGHT PF-03 FAIL" in out)
    (sb.root / "missing.json").write_text("{}")
    code, out = sb.run("preflight", "--root", str(sb.root))
    r.check("settings file present passes", "PREFLIGHT PF-03 PASS" in out and "PREFLIGHT PF-04 PASS" in out)
    r.check("stage plan and caps pass", "PREFLIGHT PF-06 PASS" in out and "PREFLIGHT PF-07 PASS" in out)
finally:
    sb.close()

reset_data()
sys.exit(r.finish())
