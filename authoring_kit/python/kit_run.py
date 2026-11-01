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
Exit codes: 0 pass, 1 check failed, 2 setup error, 3 action needed, 4 stopped.
"""
from __future__ import annotations

import argparse
import secrets
import shutil
import sys
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

PASS, FAIL, ACTION, STOPPED, SETUP = 0, 1, 3, 4, 2
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
        self.out.trust(terms=self.compat.get("rule_ids", []),
                       path_keys=set(self.compat.get("property_names", [])) | K.kit_schema_keys())

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
    def init(self, root: Path, brief: Path | None, seed: int | None, mode: str | None, review: bool) -> int:
        if (self.cp / "state.json").exists():
            raise K.KitError("ERR_WS_EXISTS", code=SETUP)
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
        }
        Budget(self.state)
        self.save()
        self.history("init", "S1")
        self.out.say("SEEDS_CHOSEN")
        self.out.say("INIT_OK")
        return PASS

    # ------------------------------------------------------------ next
    def next(self, run_all: bool = False) -> int:
        self.load()
        if not run_all or self.state["mode"] != "A":
            code = self._next_once()
            return PASS if code == DONE else code
        while True:
            if self.state["status"] != "active":
                return STOPPED
            code = self._repair_once() if self.state.get("failure") else self._next_once()
            if code == DONE:
                return PASS
            if code not in (PASS, FAIL):
                return code

    def _next_once(self) -> int:
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
            self.out.say("NEXT_READY", current["unit"])
            self.out.say("NEXT_PROMPT", current["unit"])
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
        code, usage = run_agent(self.cfg, sdir, prompt, budget.unit_cap(stage),
                                int(self.lim["timeouts"]["stage_minutes"]) * 60)
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
        sdir = self.ws / "stages" / cur["unit"]
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
        self.state["outputs_dir"][target] = str(sdir)
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
                                 "outputs_dir": self.state["outputs_dir"].get(unit, str(self.ws / "stages" / unit))}
        self.save()
        self.history("gate_fail", unit, RB.error_ids(own))
        return FAIL

    # ------------------------------------------------------------ repair
    def repair(self) -> int:
        self.load()
        return self._repair_once()

    def _repair_once(self) -> int:
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
        warns = sum(1 for x in findings if x["sev"] == CC.WARN)
        self.out.say("FINISH_COUNTS", len(self.state["s3_owners"]), len(claims), n_claims, warns)
        Budget(self.state).report(self.out)
        self.out.say("FINISH_PASS")
        return PASS

    # ------------------------------------------------------------ status
    def status(self) -> int:
        self.load()
        units = self.units()
        self.out.say("STATUS_LINE", sum(1 for u in units if u in self.state["done"]), len(units))
        self.out.say({"active": "STATUS_ACTIVE", "aborted": "STATUS_ABORTED", "finished": "STATUS_FINISHED"}[self.state["status"]])
        if self.state.get("failure"):
            self.out.say("NEXT_REPAIR_NEEDED", self.state["failure"]["unit"])
        Budget(self.state).report(self.out)
        return PASS


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["init", "next", "check", "repair", "finish", "status"])
    ap.add_argument("--ws", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--brief", default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--mode", choices=["A", "B", "a", "b"], default=None)
    ap.add_argument("--review", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args(argv)
    run = Run(Path(args.ws))
    try:
        if args.command == "init":
            return run.init(Path(args.root), Path(args.brief) if args.brief else None, args.seed, args.mode, args.review)
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
