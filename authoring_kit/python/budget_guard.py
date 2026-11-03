"""budget_guard: turn and cost caps per stage, per repaired unit and per run.

Turns are counted from the agent's own usage report when Mode A provides one;
otherwise each invocation is charged its full unit cap, which over-counts on
purpose. Costs are what the agent reports, scaled by reported_multiplier to what
the provider charges. A run that reports usage elsewhere but not this time (a
timeout, a crash) is charged a conservative share of its stage's cost cap, so a
silent failure can never slip past the caps.

Each repaired unit has its own turn pool (repair_target_caps), so one long repair
can no longer starve the repair of a different unit. A resumed run starts a new
pass: counters reset, earlier passes are kept in `passes`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402


class Budget:
    def __init__(self, state: dict):
        self.state = state.setdefault("budget", {"turns": {}, "cost_usd": {}, "invocations": 0})
        self.state.setdefault("repair_turns", {})
        self.lim = K.data("limits")

    # ---------------------------------------------------------------- totals
    def stage_turns(self, stage: str) -> int:
        return int(self.state["turns"].get(stage, 0))

    def run_turns(self) -> int:
        return sum(int(v) for v in self.state["turns"].values())

    def run_cost(self) -> float:
        return sum(float(v) for v in self.state["cost_usd"].values())

    def previous_cost(self) -> float:
        return sum(float(p.get("cost_usd", 0.0)) for p in self.state.get("passes", []))

    # ---------------------------------------------------------------- caps
    def unit_cap(self, stage: str, target_stage: str | None = None) -> int:
        """Turns one invocation may use. A repair (S5) is capped by the stage it repairs."""
        t = self.lim["turns"]
        if stage == "S5" and target_stage and target_stage in t.get("repair_unit_caps", {}):
            return int(t["repair_unit_caps"][target_stage])
        return int(t["unit_caps"][stage])

    def _stage_cap(self, stage: str) -> int:
        return int(self.lim["turns"]["stage_caps"][stage])

    def can_start(self, stage: str, target_stage: str | None = None, target: str | None = None) -> tuple[bool, str]:
        t = self.lim["turns"]
        need = self.unit_cap(stage, target_stage)
        if stage == "S5" and target and target_stage in t.get("repair_target_caps", {}):
            if int(self.state["repair_turns"].get(target, 0)) + need > int(t["repair_target_caps"][target_stage]):
                return False, "TARGET"
        if self.stage_turns(stage) + need > self._stage_cap(stage):
            return False, "STAGE"
        if self.run_turns() + need > t["run_cap"]:
            return False, "RUN"
        c = self.lim["cost_usd_unverified"]
        if self.state["cost_usd"]:
            if self.run_cost() >= c["run_cap"]:
                return False, "RUN"
            if float(self.state["cost_usd"].get(stage, 0.0)) >= c["stage_caps"].get(stage, c["run_cap"]):
                return False, "STAGE"
        return True, ""

    def unknown_charge(self, stage: str, target_stage: str | None = None) -> float:
        c = self.lim["cost_usd_unverified"]
        cap = float(c["stage_caps"].get(stage, c["run_cap"]))
        share = self.unit_cap(stage, target_stage) / max(1, self._stage_cap(stage))
        return round(cap * min(1.0, share), 2)

    # ---------------------------------------------------------------- record
    def record(self, stage: str, turns: int | None, cost: float | None = None,
               target_stage: str | None = None, target: str | None = None,
               usage_expected: bool = False) -> float | None:
        """Record one invocation. Returns the cost charged when it had to be estimated."""
        charged = (int(turns) if isinstance(turns, (int, float)) and turns >= 0
                   else self.unit_cap(stage, target_stage))
        self.state["turns"][stage] = self.stage_turns(stage) + charged
        if stage == "S5" and target:
            self.state["repair_turns"][target] = int(self.state["repair_turns"].get(target, 0)) + charged
        self.state["invocations"] = int(self.state.get("invocations", 0)) + 1
        mult = float(self.lim["cost_usd_unverified"].get("reported_multiplier", 1.0))
        estimated = None
        if isinstance(cost, (int, float)) and cost >= 0:
            amount = float(cost) * mult
        elif usage_expected:
            amount = estimated = self.unknown_charge(stage, target_stage)
            self.state["cost_unknown"] = int(self.state.get("cost_unknown", 0)) + 1
        else:
            self.state["cost_unknown"] = int(self.state.get("cost_unknown", 0)) + 1
            return None
        self.state["cost_usd"][stage] = float(self.state["cost_usd"].get(stage, 0.0)) + amount
        return estimated

    def cost_unknown(self) -> int:
        return int(self.state.get("cost_unknown", 0))

    def new_pass(self) -> None:
        """Start a fresh pass for a resumed run; keep what the earlier pass spent."""
        self.state.setdefault("passes", []).append({
            "turns": self.run_turns(), "cost_usd": round(self.run_cost(), 4),
            "invocations": int(self.state.get("invocations", 0))})
        self.state["turns"] = {}
        self.state["cost_usd"] = {}
        self.state["repair_turns"] = {}
        self.state["invocations"] = 0

    # ---------------------------------------------------------------- report
    def report(self, out: K.Out, stage: str | None = None) -> None:
        t = self.lim["turns"]
        if stage:
            out.say("BUDGET_STAGE", stage, self.stage_turns(stage), t["stage_caps"][stage])
        out.say("BUDGET_RUN", self.run_turns(), t["run_cap"])
        if self.state["cost_usd"]:
            out.say("BUDGET_COST", round(self.run_cost(), 2), float(self.lim["cost_usd_unverified"]["run_cap"]))
