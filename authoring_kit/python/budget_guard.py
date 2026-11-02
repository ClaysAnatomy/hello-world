"""budget_guard: turn caps per stage and per run.

Turns are counted from the agent's own usage report when Mode A provides one;
otherwise each invocation is charged its full unit cap, which over-counts on
purpose. Dollar figures are tracked only when reported and are UNVERIFIED
estimates; the guard prints turn counts only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402


class Budget:
    def __init__(self, state: dict):
        self.state = state.setdefault("budget", {"turns": {}, "cost_usd": {}, "invocations": 0})
        self.lim = K.data("limits")

    def stage_turns(self, stage: str) -> int:
        return int(self.state["turns"].get(stage, 0))

    def run_turns(self) -> int:
        return sum(int(v) for v in self.state["turns"].values())

    def run_cost(self) -> float:
        return sum(float(v) for v in self.state["cost_usd"].values())

    def unit_cap(self, stage: str, target_stage: str | None = None) -> int:
        """Turns one invocation may use. A repair (S5) is capped by the stage it repairs."""
        t = self.lim["turns"]
        if stage == "S5" and target_stage and target_stage in t.get("repair_unit_caps", {}):
            return int(t["repair_unit_caps"][target_stage])
        return int(t["unit_caps"][stage])

    def can_start(self, stage: str, target_stage: str | None = None) -> tuple[bool, str]:
        t = self.lim["turns"]
        need = self.unit_cap(stage, target_stage)
        if self.stage_turns(stage) + need > t["stage_caps"][stage]:
            return False, "STAGE"
        if self.run_turns() + need > t["run_cap"]:
            return False, "RUN"
        c = self.lim["cost_usd_unverified"]
        if self.state["cost_usd"]:
            if self.run_cost() >= c["run_cap"]:
                return False, "RUN"
            if float(self.state["cost_usd"].get(stage, 0.0)) >= c["stage_caps"][stage]:
                return False, "STAGE"
        return True, ""

    def record(self, stage: str, turns: int | None, cost: float | None = None,
               target_stage: str | None = None) -> None:
        charged = (int(turns) if isinstance(turns, (int, float)) and turns >= 0
                   else self.unit_cap(stage, target_stage))
        self.state["turns"][stage] = self.stage_turns(stage) + charged
        self.state["invocations"] = int(self.state.get("invocations", 0)) + 1
        if isinstance(cost, (int, float)) and cost >= 0:
            self.state["cost_usd"][stage] = float(self.state["cost_usd"].get(stage, 0.0)) + float(cost)
        else:
            self.state["cost_unknown"] = int(self.state.get("cost_unknown", 0)) + 1

    def cost_unknown(self) -> int:
        return int(self.state.get("cost_unknown", 0))

    def report(self, out: K.Out, stage: str | None = None) -> None:
        t = self.lim["turns"]
        if stage:
            out.say("BUDGET_STAGE", stage, self.stage_turns(stage), t["stage_caps"][stage])
        out.say("BUDGET_RUN", self.run_turns(), t["run_cap"])
