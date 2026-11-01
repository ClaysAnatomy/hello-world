"""kit_run: the authoring kit's command line.

PowerShell, from the project root:
    python authoring_kit\\python\\kit_run.py init   --ws <folder> --root . [--brief <file>] [--seed N] [--mode A|B] [--review]
    python authoring_kit\\python\\kit_run.py next   --ws <folder> [--all]
    python authoring_kit\\python\\kit_run.py check  --ws <folder>
    python authoring_kit\\python\\kit_run.py repair --ws <folder>
    python authoring_kit\\python\\kit_run.py finish --ws <folder>
    python authoring_kit\\python\\kit_run.py status --ws <folder>

The workspace folder is the sealed case folder (for this project,
<vault_dir>\\<case_id>); the kit never knows or prints a vault path. Every
line printed is a fixed sentence with IDs, paths, counts or PASS/FAIL.
Exit codes: 0 pass, 1 check failed, 2 setup error, 3 action needed, 4 stopped,
5 paused (a usage limit was reached; run next again later).

Also:
    python authoring_kit\\python\\kit_run.py audit       --ws <folder> --bundle <player bundle json>
    python authoring_kit\\python\\kit_run.py audit-score --ws <folder>
    python authoring_kit\\python\\kit_run.py estimate    --documents N [--repairs R] [--review]
"""
from __future__ import annotations

import argparse
import secrets
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402
import brief_builder as BB  # noqa: E402
import case_checks as CC  # noqa: E402
import repair_builder as RB  # noqa: E402
import voice_lint as VL  # noqa: E402
from budget_guard import Budget  # noqa: E402
from compat_check import print_report, run_compat  # noqa: E402
from ledger import Ledger, seed_items  # noqa: E402
from runners import run_agent, run_engine_check  # noqa: E402
from seed_sampler import sample  # noqa: E402

PASS, FAIL, ACTION, STOPPED, SETUP, PAUSED = 0, 1, 3, 4, 2, 5
DONE = 10  # internal: nothing left to do


class Run:
    def __init__(self, ws: Path, out: K.Out | None = None):
        self.ws = ws.resolve()
        self.cp = self.ws / "checkpoints"
        self.cfg = K.data("kit_config")
        self.lim = K.data("limits")
        self.plan_cfg = K.data("stage_plan")
        self.out = out or K.Out()
        self.state: dict = {}
        self.compat: dict = {}

    # ------------------------------------------------------------ state
    def load(self) -> None:
        sp = self.cp / "state.json"
        if not sp.is_file():
            raise K.KitError("ERR_NO_STATE", code=SETUP)
        self.state = K.load_json(sp)
        self.compat = K.load_json(self.cp / "compat.json")
        self._trust()

    def save(self) -> None:
        K.dump_json(self.state, self.cp / "state.json")

    def _trust(self) -> None:
        terms = list(self.compat.get("rule_ids", []))
        if self.state.get("stage_root"):
            terms.append(self.state["stage_root"])
        self.out.trust(terms=terms,
                       path_keys=set(self.compat.get("property_names", [])) | K.kit_schema_keys())

    # ------------------------------------------------------------ stage folders
    MARKER = ".mm_kit_stage_root"

    @property
    def stage_root(self) -> Path:
        return Path(self.state["stage_root"])

    def _ensure_stage_root(self) -> None:
        sr = self.stage_root
        sr.mkdir(parents=True, exist_ok=True)
        (sr / self.MARKER).write_text("authoring kit stage folders; safe to delete\n", encoding="utf-8")

    def _close_dir(self, name: str) -> None:
        """Delete one stage folder, only if it sits directly in the marked stage root."""
        sr = self.stage_root
        d = sr / name
        if d.is_dir() and d.parent == sr and (sr / self.MARKER).is_file():
            shutil.rmtree(d, ignore_errors=True)

    def _close_unit(self, target: str) -> None:
        self._close_dir(target)
        for d in list(self.stage_root.glob(f"S5-{target}-R*")):
            self._close_dir(d.name)

    @property
    def root(self) -> Path:
        return Path(self.state["root"])

    def history(self, event: str, unit: str, ids: list[str] | None = None) -> None:
        hp = self.cp / "history.json"
        h = K.load_json(hp) if hp.is_file() else []
        h.append({"event": event, "unit": unit, "ids": ids or []})
        K.dump_json(h, hp)

    # ------------------------------------------------------------ units
    def units(self) -> list[str]:
        u = ["S1", "S2"]
        u += [f"S3-{o}" for o in self.state.get("s3_owners", [])]
        if self.state.get("s2_done"):
            u.append("S3_GATE")
            if self.state.get("has_s4"):
                u.append("S4")
            if self.state.get("review"):
                u.append("S6")
        return u

    def next_unit(self) -> str | None:
        for u in self.units():
            if u not in self.state["done"]:
                return u
        return None

    @staticmethod
    def stage_of(unit: str) -> str:
        return unit.split("-")[0] if unit.startswith("S3-") else unit

    def owner_of(self, unit: str) -> str | None:
        if unit.startswith("S3-"):
            return unit[3:]
        if unit == "S4":
            return self.plan_cfg["s4_owner"]
        return None

    # ------------------------------------------------------------ init
    def init(self, root: Path, brief: Path | None, seed: int | None, mode: str | None, review: bool,
             stage_root: Path | None = None) -> int:
        if (self.cp / "state.json").exists():
            raise K.KitError("ERR_WS_EXISTS", code=SETUP)
        sr = stage_root or (Path(self.cfg["stage_root"]) if self.cfg.get("stage_root") else None)
        sr = (sr or Path(tempfile.mkdtemp(prefix="mm_kit_stages_"))).resolve()
        try:
            sr.relative_to(self.ws)
            raise K.KitError("ERR_STAGE_ROOT_IN_WS", code=SETUP)
        except ValueError:
            pass
        report = run_compat(root.resolve())
        code = print_report(report, self.out)
        if code != 0:
            self.out.say("INIT_FAIL")
            return code
        self.compat = report
        self._trust()
        ledger = Ledger.load(root / self.cfg["state"]["ledger"])
        tp = root / self.cfg["state"]["taste_profile"]
        taste = K.load_json(tp) if tp.is_file() else {}
        seed = seed if seed is not None else secrets.randbits(31)
        seeds = sample(seed, report, ledger, taste)
        self.cp.mkdir(parents=True, exist_ok=True)
        K.dump_json(report, self.cp / "compat.json")
        K.dump_json(seeds, self.cp / "seeds.json")
        if brief is not None:
            try:
                shutil.copyfile(brief, self.cp / "brief.md")
            except OSError:
                raise K.KitError("ERR_BAD_BRIEF", code=SETUP)
        self.state = {
            "kit_version": K.data("kit_config")["version"], "run_ref": secrets.token_hex(8),
            "root": str(root.resolve()), "mode": (mode or self.cfg["mode"]).upper(),
            "status": "active", "done": [], "s3_owners": [], "has_s4": False, "s2_done": False,
            "review": bool(review or self.cfg.get("run_optional_S6")), "current": None,
            "failure": None, "gate_failures": 0, "outputs_dir": {}, "placed": {},
            "stage_root": str(sr),
        }
        Budget(self.state)
        self._ensure_stage_root()
        self._trust()
        self.save()
        self.history("init", "S1")
        self.out.say("SEEDS_CHOSEN")
        self.out.say("STAGE_ROOT", self.state["stage_root"])
        self.out.say("INIT_OK")
        return PASS

    # ------------------------------------------------------------ next
    def next(self, run_all: bool = False) -> int:
        self.load()
        if not run_all or self.state["mode"] != "A":
            code = self._next_once()
            return PASS if code == DONE else code
        while True:
            if self.state["status"] not in ("active", "paused"):
                return STOPPED
            code = self._repair_once() if self.state.get("failure") else self._next_once()
            if code == DONE:
                return PASS
            if code not in (PASS, FAIL):
                return code

    def _next_once(self) -> int:
        if self.state["status"] == "paused" and self.state.get("current"):
            self.state["status"] = "active"
            self.save()
            return self._dispatch(self.state["current"])
        if self.state["status"] != "active":
            self.out.say("ERR_NOT_ACTIVE")
            return STOPPED
        if self.state.get("failure"):
            self.out.say("NEXT_REPAIR_NEEDED", self.state["failure"]["unit"])
            return ACTION
        cur = self.state.get("current")
        if cur and self.state["mode"] == "B":
            self.out.say("NEXT_WAITING", cur["unit"])
            return ACTION
        unit = self.next_unit()
        if unit is None:
            self.out.say("NEXT_DONE")
            return DONE
        if unit == "S3_GATE":
            return self._gate()
        stage = self.stage_of(unit)
        current = {"unit": unit, "stage": stage, "owner": self.owner_of(unit), "target": unit, "round": 0}
        return self._dispatch(current)

    def _dispatch(self, current: dict) -> int:
        prompt = BB.prepare(current, self.ws, self.root, self.state)
        self.state["current"] = current
        self.save()
        self.history("prepared", current["unit"])
        if self.state["mode"] == "B":
            self.out.trust(terms=[str(prompt)])
            self.out.say("NEXT_READY", current["unit"])
            self.out.say("NEXT_PROMPT", str(prompt))
            return ACTION
        budget = Budget(self.state)
        stage = current["stage"]
        ok, why = budget.can_start(stage)
        if not ok:
            self.state["current"] = None
            self.save()
            self.out.say("BUDGET_STOP_STAGE" if why == "STAGE" else "BUDGET_STOP_RUN", stage)
            budget.report(self.out, stage)
            return STOPPED
        sdir = prompt.parent
        self.out.say("AGENT_STARTED", current["unit"])
        code, usage, paused = run_agent(self.cfg, sdir, prompt, budget.unit_cap(stage),
                                        int(self.lim["timeouts"]["stage_minutes"]) * 60, stage=stage)
        outputs = K.load_json(sdir / "unit.json")["outputs"]
        if paused and not all((sdir / o).is_file() for o in outputs):
            budget.record(stage, usage.get("turns", 1), usage.get("cost_usd"))
            self.state["status"] = "paused"
            self.save()
            self.history("paused", current["unit"])
            self.out.say("AGENT_PAUSED", current["unit"])
            budget.report(self.out, stage)
            return PAUSED
        budget.record(stage, usage.get("turns"), usage.get("cost_usd"))
        self.save()
        if code == 124:
            self.out.say("AGENT_TIMEOUT", current["unit"])
        else:
            self.out.say("AGENT_EXIT", current["unit"], code)
        budget.report(self.out, stage)
        return self.check(loaded=True)

    # ------------------------------------------------------------ check
    def check(self, loaded: bool = False) -> int:
        if not loaded:
            self.load()
        cur = self.state.get("current")
        if not cur:
            self.out.say("ERR_NOTHING_TO_CHECK")
            return ACTION
        if self._drifted():
            return STOPPED
        sdir = self.stage_root / cur["unit"]
        target = cur["target"]
        tstage = self.stage_of(target)
        findings = self._evaluate(tstage, target, sdir)
        errors = [f for f in findings if f["sev"] == CC.ERROR]
        self._print_findings(findings)
        if errors:
            self.out.say("CHECK_FAIL", target)
            self.history("fail", target, RB.error_ids(findings))
            return self._record_failure(target, findings, cur["round"], sdir)
        self.out.say("CHECK_PASS", target)
        self.history("pass", target)
        self._accept(tstage, target, sdir)
        self.state["current"] = None
        self.state["failure"] = None
        self.save()
        if self.next_unit() == "S3_GATE":
            return self._gate()
        return PASS

    def _print_findings(self, findings: list[dict]) -> None:
        for f in findings:
            self.out.say("CHECK_FINDING_FAIL" if f["sev"] == CC.ERROR else "CHECK_FINDING_WARN", f["id"], f["path"])
        n_err = sum(1 for f in findings if f["sev"] == CC.ERROR)
        self.out.say("CHECK_COUNTS", n_err, len(findings) - n_err)

    def _record_failure(self, target: str, findings: list[dict], attempt_round: int, outputs_dir: Path) -> int:
        prev = self.state.get("failure") if self.state.get("failure", {}) and self.state["failure"].get("unit") == target else None
        decision = RB.decide(prev, findings, attempt_round)
        ids = RB.error_ids(findings)
        if decision != RB.REPAIR:
            self.state["status"] = "aborted"
            self.state["current"] = None
            self.save()
            self.out.say("ABORT_REPEAT" if decision == RB.ABORT_REPEAT else "ABORT_CAP", target)
            for i in ids:
                self.out.say("ABORT_LINE", i)
            self.history("abort", target, ids)
            return STOPPED
        history = (prev.get("history", []) if prev else []) + [ids]
        self.state["failure"] = {"unit": target, "findings": [f for f in findings if f["sev"] == CC.ERROR],
                                 "round": attempt_round, "history": history, "outputs_dir": str(outputs_dir)}
        self.state["current"] = None
        self.save()
        return FAIL

    def _drifted(self) -> bool:
        for rel, digest in self.compat.get("engine_files", {}).items():
            p = self.root / rel
            if not p.is_file() or K.sha256_file(p) != digest:
                self.state["status"] = "aborted"
                self.save()
                self.out.say("ABORT_DRIFT")
                self.out.say("ABORT_LINE", "KT-RN-02")
                return True
        return False

    # ------------------------------------------------------------ evaluation
    def _evaluate(self, stage: str, target: str, sdir: Path) -> list[dict]:
        seeds = K.load_json(self.cp / "seeds.json")
        if stage == "S1":
            p = sdir / "bible.json"
            bible = self._read(p)
            if bible is None:
                return [CC.F("KT-BI-01")]
            f = CC.check_bible(bible, seeds)
            if not CC.has_errors(f):
                f += VL.lint_bible_names(bible)
            return f
        if stage == "S2":
            plan, case, skin = (self._read(sdir / n) for n in ("clue_plan.json", "case.json", "skin.json"))
            if plan is None or case is None or skin is None:
                return [CC.F("KT-PL-01")]
            bible = K.load_json(self.cp / "bible.json")
            f = CC.check_plan(plan, bible, case, seeds, self.plan_cfg["s4_owner"])
            if CC.has_errors(f):
                return f
            return f + self._engine("S2", sdir / "case.json", sdir / "skin.json")
        if stage in ("S3", "S4"):
            fill = self._read(sdir / "fill.json")
            if fill is None:
                return [CC.F("KT-FL-01")]
            owner = self.owner_of(target)
            plan = K.load_json(self.cp / "clue_plan.json")
            bible = K.load_json(self.cp / "bible.json")
            f = VL.lint_fill(fill, owner, plan, bible)
            if stage == "S4" and not CC.has_errors(f):
                fills = self._fills()
                fills[owner] = fill
                case_path, skin_path = self._write_case(fills)
                f += self._engine("S4", case_path, skin_path)
            return f
        if stage == "S6":
            rv = self._read(sdir / "review.json")
            if rv is None or K.schema_errors(rv, K.schema("review")):
                return [CC.F("KT-RV-01")]
            need = {i["id"] for i in K.data("rubric")["items"] if i["tag"] == "SECOND-MODEL"}
            fm = {m["id"] for m in K.data("failure_modes")["modes"]}
            if set(rv["scores"]) != need or any(x.startswith("FM") and x not in fm for x in rv["flags"]):
                return [CC.F("KT-RV-01")]
            return []
        return []

    @staticmethod
    def _read(p: Path):
        try:
            return K.load_json(p)
        except (OSError, ValueError):
            return None

    def _engine(self, at: str, case: Path, skin: Path) -> list[dict]:
        tol = self.lim["tolerated_engine_rules"].get(at, []) if at in ("S2", "S3_GATE") else []
        out: list[dict] = []
        for chk in self.cfg["engine_checks"]:
            if not chk.get("enabled") or at not in chk["at"]:
                continue
            code, text = run_engine_check(self.root, self.cfg, chk, case, skin, self.ws,
                                          int(self.lim["timeouts"]["engine_check_seconds"]))
            out += RB.parse_engine_output(text, code, chk["id"], self.compat.get("rule_ids", []), tol)
            del text
        return out

    # ------------------------------------------------------------ accept
    def _fills(self) -> dict[str, dict]:
        out = {}
        d = self.cp / "fills"
        if d.is_dir():
            for p in sorted(d.glob("*.json")):
                obj = K.load_json(p)
                out[obj["owner"]] = obj
        return out

    def _write_case(self, fills: dict[str, dict]) -> tuple[Path, Path]:
        skeleton = K.load_json(self.cp / "skeleton.json")
        texts = {tok: txt for f in fills.values() for tok, txt in f["fills"].items()}
        case, placed = K.rebuild_case(skeleton, texts)
        cpath = self.ws / self.cfg["workspace"]["case_file"]
        spath = self.ws / self.cfg["workspace"]["skin_file"]
        K.dump_json(case, cpath)
        K.copy_file(self.cp / "skin.json", spath)
        self.state["placed"] = placed
        return cpath, spath

    def _accept(self, stage: str, target: str, sdir: Path) -> None:
        archive = self.cp / "units" / target
        if archive.exists():
            shutil.rmtree(archive)
        archive.mkdir(parents=True)
        for name in K.load_json(sdir / "unit.json")["outputs"] + ["prompt.md", "unit.json"]:
            if (sdir / name).is_file():
                K.copy_file(sdir / name, archive / name)
        self.state["outputs_dir"][target] = str(archive)
        if stage == "S1":
            K.copy_file(sdir / "bible.json", self.cp / "bible.json")
        elif stage == "S2":
            K.copy_file(sdir / "case.json", self.cp / "skeleton.json")
            K.copy_file(sdir / "skin.json", self.cp / "skin.json")
            K.copy_file(sdir / "clue_plan.json", self.cp / "clue_plan.json")
            plan = K.load_json(self.cp / "clue_plan.json")
            owners = CC.s3_owners(plan)
            self.state["s3_owners"] = owners
            self.state["has_s4"] = any(ph["stage"] == "S4" for ph in plan["placeholders"])
            self.state["s2_done"] = True
            # keep earlier fills only where the owner's tokens are unchanged
            for owner, fill in self._fills().items():
                tokens = {ph["token"] for ph in plan["placeholders"] if ph["owner"] == owner}
                if set(fill["fills"]) != tokens:
                    (self.cp / "fills" / f"{owner}.json").unlink()
                    unit = "S4" if owner == self.plan_cfg["s4_owner"] else f"S3-{owner}"
                    if unit in self.state["done"]:
                        self.state["done"].remove(unit)
            for gate in ("S3_GATE",):
                if gate in self.state["done"]:
                    self.state["done"].remove(gate)
            self._write_case(self._fills())
        elif stage in ("S3", "S4"):
            fill = K.load_json(sdir / "fill.json")
            K.dump_json(fill, self.cp / "fills" / f"{fill['owner']}.json")
            self._write_case(self._fills())
        elif stage == "S6":
            rv = K.load_json(sdir / "review.json")
            K.dump_json(rv, self.cp / "review.json")
            for rid in sorted(rv["scores"]):
                self.out.say("REVIEW_SCORE", rid, rv["scores"][rid])
            for fl in rv["flags"]:
                self.out.say("REVIEW_FLAG", fl)
        if target not in self.state["done"]:
            self.state["done"].append(target)
        self._close_unit(target)

    # ------------------------------------------------------------ gate
    def _gate(self) -> int:
        plan = K.load_json(self.cp / "clue_plan.json")
        fills = self._fills()
        owners = self.state["s3_owners"]
        s3fills = {o: fills[o] for o in owners if o in fills}
        findings = VL.lint_overlap(s3fills, owners)
        case_path, skin_path = self._write_case(fills)
        eng = self._engine("S3_GATE", case_path, skin_path)
        placed = self.state.get("placed", {})
        tok_owner = {ph["token"]: ph["owner"] for ph in plan["placeholders"]}
        for f in eng:
            owner = None
            for tok, path in placed.items():
                if f["path"] != "$" and (path.startswith(f["path"]) or f["path"].startswith(path)):
                    owner = tok_owner.get(tok)
                    break
            f["path"] = owner or f["path"]
            f["owner"] = owner
            findings.append(f)
        errors = [f for f in findings if f["sev"] == CC.ERROR]
        self._print_findings(findings)
        if not errors:
            self.out.say("GATE_PASS", "S3")
            self.state["done"].append("S3_GATE")
            self.save()
            return PASS
        self.out.say("GATE_FAIL", "S3")
        self.state["gate_failures"] = int(self.state.get("gate_failures", 0)) + 1
        if self.state["gate_failures"] > self.lim["repair"]["max_repair_rounds"]:
            self.state["status"] = "aborted"
            self.save()
            self.out.say("ABORT_GATE", "S3")
            for i in RB.error_ids(findings):
                self.out.say("ABORT_LINE", i)
            return STOPPED
        # blame the first owner named, else the structure (S2)
        blamed = next((f["path"] for f in errors if f["path"] in owners), None)
        unit = f"S3-{blamed}" if blamed else "S2"
        if unit in self.state["done"]:
            self.state["done"].remove(unit)
        own = [f for f in errors if (blamed and f["path"] == blamed) or (not blamed)]
        self.state["failure"] = {"unit": unit, "findings": own, "round": 0, "history": [RB.error_ids(own)],
                                 "outputs_dir": self.state["outputs_dir"].get(unit, str(self.cp / "units" / unit))}
        self.save()
        self.history("gate_fail", unit, RB.error_ids(own))
        return FAIL

    # ------------------------------------------------------------ repair
    def repair(self) -> int:
        self.load()
        return self._repair_once()

    def _repair_once(self) -> int:
        if self.state["status"] == "paused" and self.state.get("current"):
            return self._next_once()
        if self.state["status"] != "active":
            self.out.say("ERR_NOT_ACTIVE")
            return STOPPED
        fail = self.state.get("failure")
        if not fail:
            self.out.say("ERR_NO_FAILURE")
            return ACTION
        rnd = int(fail["round"]) + 1
        if rnd > self.lim["repair"]["max_repair_rounds"]:
            self.state["status"] = "aborted"
            self.save()
            self.out.say("ABORT_CAP", fail["unit"])
            return STOPPED
        unit = f"S5-{fail['unit']}-R{rnd}"
        current = {"unit": unit, "stage": "S5", "owner": self.owner_of(fail["unit"]),
                   "target": fail["unit"], "round": rnd}
        self.out.say("REPAIR_READY", fail["unit"], rnd)
        return self._dispatch(current)

    # ------------------------------------------------------------ finish
    def finish(self) -> int:
        self.load()
        if self.state["status"] != "active":
            self.out.say("ERR_NOT_ACTIVE")
            return STOPPED
        if self.next_unit() is not None or self.state.get("failure") or self.state.get("current"):
            self.out.say("FINISH_FAIL")
            return ACTION
        if self._drifted():
            return STOPPED
        fills = self._fills()
        case_path, skin_path = self._write_case(fills)
        rx = K.placeholder_search_regex(self.lim["ids"]["placeholder_format"])
        findings = []
        if any(rx.search(s) for s in K.string_leaves(K.load_json(case_path))):
            findings.append(CC.F("KT-RN-01"))
        findings += self._engine("FINISH", case_path, skin_path)
        self._print_findings(findings)
        if CC.has_errors(findings):
            self.out.say("FINISH_FAIL")
            return FAIL
        placed = self.state.get("placed", {})
        claims = []
        n_claims = 0
        for owner, f in sorted(fills.items()):
            for tok in sorted(f["fills"]):
                facts = sorted(f["claims"].get(tok, []))
                n_claims += len(facts)
                claims.append({"path": placed.get(tok, "$"), "owner": owner, "facts": facts})
        K.dump_json({"version": 1, "claims": claims}, self.ws / "claims.json")
        seeds = K.load_json(self.cp / "seeds.json")
        ledger = Ledger.load(self.root / self.cfg["state"]["ledger"])
        ledger.append(self.state["run_ref"], seed_items(seeds))
        ledger.save()
        self.state["status"] = "finished"
        self.save()
        self.history("finish", "FINISH")
        sr = self.stage_root
        if (sr / self.MARKER).is_file():
            shutil.rmtree(sr, ignore_errors=True)
        warns = sum(1 for x in findings if x["sev"] == CC.WARN)
        self.out.say("FINISH_COUNTS", len(self.state["s3_owners"]), len(claims), n_claims, warns)
        Budget(self.state).report(self.out)
        self.out.say("FINISH_PASS")
        return PASS

    # ------------------------------------------------------------ blind audit (S7)
    AUDIT_MODES = ("SHORTCUT", "SOLVE")

    def audit(self, bundle_path: Path) -> int:
        """Prepare (and in Mode A run) the cross-family blind audit on the player bundle."""
        self.load()
        if self.state["status"] != "finished":
            self.out.say("ERR_AUDIT_NOT_FINISHED")
            return ACTION
        fa = (self.cfg["agent"].get("family") or "").strip().lower()
        fb = (self.cfg["audit_agent"].get("family") or "").strip().lower()
        if not fa or not fb or fa == fb:
            self.out.say("ERR_AUDIT_FAMILY")
            return SETUP
        try:
            bundle = K.load_json(bundle_path)
        except (OSError, ValueError):
            self.out.say("ERR_BAD_BUNDLE")
            return SETUP
        self._ensure_stage_root()
        prompts = {mode: BB.prepare_audit(mode, self.ws, bundle, self.state) for mode in self.AUDIT_MODES}
        self.state["audit"] = {"status": "prepared"}
        self.save()
        if self.state["mode"] == "B":
            for mode, prompt in prompts.items():
                self.out.trust(terms=[str(prompt)])
                self.out.say("AUDIT_READY", f"S7-{mode}")
                self.out.say("NEXT_PROMPT", str(prompt))
            return ACTION
        cap = int(self.lim["turns"]["unit_caps"]["S7"])
        for mode, prompt in prompts.items():
            unit = f"S7-{mode}"
            self.out.say("AGENT_STARTED", unit)
            code, _usage, paused = run_agent(self.cfg, prompt.parent, prompt, cap,
                                             int(self.lim["timeouts"]["stage_minutes"]) * 60,
                                             stage="S7", agent_key="audit_agent")
            if paused and not (prompt.parent / "answers.json").is_file():
                self.out.say("AGENT_PAUSED", unit)
                return PAUSED
            self.out.say("AGENT_EXIT", unit, code)
        return self.audit_score(loaded=True)

    def audit_score(self, loaded: bool = False) -> int:
        """Score the audit answers against the sealed key. Prints verdicts, numbers and IDs only."""
        if not loaded:
            self.load()
        acfg = self.lim["audit"]
        self.out.trust(terms=["PASS", "FAIL"])
        bible = K.load_json(self.cp / "bible.json")
        plan = K.load_json(self.cp / "clue_plan.json")
        answers = {}
        for mode in self.AUDIT_MODES:
            src = self.stage_root / f"S7-{mode}" / "answers.json"
            try:
                ans = K.load_json(src)
            except (OSError, ValueError):
                ans = None
            if ans is None or K.schema_errors(ans, K.schema("answers")) or ans.get("mode") != mode:
                self.out.say("ERR_AUDIT_ANSWERS")
                return FAIL
            answers[mode] = ans
            K.dump_json(ans, self.cp / "audit" / f"{mode}.json")
        cite_map = {}
        if self.cfg["audit"].get("cite_map"):
            try:
                cite_map = K.load_json(self.ws / self.cfg["audit"]["cite_map"])
            except (OSError, ValueError):
                cite_map = {}
        facts = {f["id"]: f for f in bible["facts"]}
        report, ok_all = {"questions": {}}, True
        for q in sorted(bible["questions"], key=lambda x: x["id"]):
            qid = q["id"]
            correct = next(o for o in q["options"] if o["correct"])
            support = set(correct["support"])
            for fid in list(support):
                support |= set(facts.get(fid, {}).get("from", []))
            gold = {c["id"] for c in plan["clues"] if set(c["facts"]) & support}
            v = answers["SOLVE"]["verdict"].get(qid, {})
            solved = v.get("selected_opt") == correct["id"]
            cited = {cite_map.get(x, x) for x in v.get("cited", [])}
            inter, union = cited & gold, cited | gold
            precision = len(inter) / len(cited) if cited else 0.0
            jaccard = len(inter) / len(union) if union else 0.0
            cited_facts = set().union(*[set(c["facts"]) for c in plan["clues"] if c["id"] in cited]) if cited else set()
            needed = set(correct["support"])
            covered = {f for f in needed if f in cited_facts
                       or (facts.get(f, {}).get("from") and set(facts[f]["from"]) <= cited_facts)}
            coverage = len(covered) / len(needed) if needed else 1.0
            cite_ok = (coverage >= acfg["min_cite_coverage"] - 1e-9
                       and (precision == 1.0 or not acfg["require_cite_precision"]))
            sv = answers["SHORTCUT"]["verdict"].get(qid, {})
            threshold = 1.0 / max(len(q["options"]), 1) + acfg["options_only_margin"]
            shortcut_ok = not (sv.get("selected_opt") == correct["id"] and float(sv.get("confidence", 0)) > threshold + 1e-9)
            self.out.say("AUDIT_RESULT", qid, "AU-01", "PASS" if solved else "FAIL")
            self.out.say("AUDIT_CITE", qid, round(precision, 2), round(coverage, 2), round(jaccard, 2))
            self.out.say("AUDIT_RESULT", qid, "AU-02", "PASS" if cite_ok else "FAIL")
            self.out.say("AUDIT_RESULT", qid, "AU-03", "PASS" if shortcut_ok else "FAIL")
            ok_all = ok_all and (solved or not acfg["require_full_solve"]) and cite_ok and shortcut_ok
            report["questions"][qid] = {"AU-01": solved, "precision": round(precision, 2), "coverage": round(coverage, 2),
                                        "jaccard": round(jaccard, 2),
                                        "AU-02": cite_ok, "AU-03": shortcut_ok}
        report["pass"] = ok_all
        K.dump_json(report, self.cp / "audit" / "report.json")
        self.state["audit"] = {"status": "scored", "pass": ok_all}
        self.save()
        for mode in self.AUDIT_MODES:
            self._close_dir(f"S7-{mode}")
        self.out.say("AUDIT_PASS" if ok_all else "AUDIT_FAIL")
        return PASS if ok_all else FAIL

    # ------------------------------------------------------------ estimate
    def estimate(self, documents: int, repairs: int, review: bool) -> int:
        t = self.lim["turns"]
        u, c = t["unit_caps"], t["stage_caps"]
        inv = 2 + documents + 1 + repairs + (1 if review else 0)
        turns = u["S1"] + u["S2"] + documents * u["S3"] + u["S4"] + repairs * u["S5"] + (u["S6"] if review else 0)
        s3 = documents * u["S3"]
        self.out.say("ESTIMATE_LINE", documents, inv, turns, t["run_cap"])
        self.out.say("ESTIMATE_S3", s3, c["S3"])
        fits = turns <= t["run_cap"] and s3 <= c["S3"] and repairs * u["S5"] <= c["S5"]
        self.out.say("ESTIMATE_FITS" if fits else "ESTIMATE_OVER")
        return PASS if fits else FAIL

    # ------------------------------------------------------------ status
    def status(self) -> int:
        self.load()
        units = self.units()
        self.out.say("STATUS_LINE", sum(1 for u in units if u in self.state["done"]), len(units))
        self.out.say({"active": "STATUS_ACTIVE", "aborted": "STATUS_ABORTED", "finished": "STATUS_FINISHED",
                      "paused": "STATUS_PAUSED"}[self.state["status"]])
        if self.state.get("failure"):
            self.out.say("NEXT_REPAIR_NEEDED", self.state["failure"]["unit"])
        Budget(self.state).report(self.out)
        return PASS


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["init", "next", "check", "repair", "finish", "status",
                                        "audit", "audit-score", "estimate"])
    ap.add_argument("--ws", default=None)
    ap.add_argument("--stage-root", default=None)
    ap.add_argument("--bundle", default=None)
    ap.add_argument("--documents", type=int, default=10)
    ap.add_argument("--repairs", type=int, default=1)
    ap.add_argument("--root", default=".")
    ap.add_argument("--brief", default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--mode", choices=["A", "B", "a", "b"], default=None)
    ap.add_argument("--review", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args(argv)
    if args.command == "estimate":
        return Run(Path(".")).estimate(args.documents, args.repairs, args.review)
    if not args.ws:
        ap.error("--ws is required")
    run = Run(Path(args.ws))
    try:
        if args.command == "init":
            return run.init(Path(args.root), Path(args.brief) if args.brief else None, args.seed, args.mode,
                            args.review, Path(args.stage_root) if args.stage_root else None)
        if args.command == "audit":
            if not args.bundle:
                ap.error("--bundle is required")
            return run.audit(Path(args.bundle))
        if args.command == "audit-score":
            return run.audit_score()
        if args.command == "next":
            return run.next(args.all)
        if args.command == "check":
            return run.check()
        if args.command == "repair":
            return run.repair()
        if args.command == "finish":
            return run.finish()
        return run.status()
    except K.KitError as e:
        run.out.say(e.msg_id, *e.args_out)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
