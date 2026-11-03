"""Kit v4.2 data changes, copied key by key from the published kit so local edits survive.

Run from the project folder (the one holding authoring_kit), pointing at the cloned kit's data folder:
    python apply_data_changes.py --from <clone>\\authoring_kit\\data --check   (report; write nothing)
    python apply_data_changes.py --from <clone>\\authoring_kit\\data           (apply)

It changes only these keys and keeps every other value, including local ones such as
limits.json -> tolerated_engine_rules and any per-stage model or effort already set:
  stage_plan.json  stages (S2 becomes S2A and S2B), inline_inputs, inline_note, inline_max_chars, s2_split_note
  limits.json      turns, cost_usd_unverified, timeouts, ids.print_prefixes (union)
  messages.json    every message the published kit has that the local file lacks
It never touches kit_config.json or capability_map.json. Running it twice is safe.
"""
import json
import sys
from pathlib import Path

LOCAL = Path("authoring_kit") / "data"
CHECK = "--check" in sys.argv
try:
    SRC = Path(sys.argv[sys.argv.index("--from") + 1])
except (ValueError, IndexError):
    sys.exit("usage: python apply_data_changes.py --from <clone>\\authoring_kit\\data [--check]")


def load(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


changed = []

# stage_plan.json
sp_l, sp_u = load(LOCAL / "stage_plan.json"), load(SRC / "stage_plan.json")
local_stage = {s["id"]: s for s in sp_l["stages"]}
stages = []
for s in sp_u["stages"]:
    s = dict(s)
    old = local_stage.get(s["id"])
    if old:
        for k in ("model", "effort"):
            if old.get(k) is not None:
                s[k] = old[k]
    stages.append(s)
if sp_l["stages"] != stages:
    sp_l["stages"] = stages
    changed.append("stage_plan.stages")
for k in ("inline_inputs", "inline_note", "inline_max_chars", "s2_split_note"):
    if sp_l.get(k) != sp_u.get(k):
        sp_l[k] = sp_u[k]
        changed.append(f"stage_plan.{k}")

# limits.json
li_l, li_u = load(LOCAL / "limits.json"), load(SRC / "limits.json")
for k in ("turns", "cost_usd_unverified", "timeouts"):
    if li_l.get(k) != li_u[k]:
        li_l[k] = li_u[k]
        changed.append(f"limits.{k}")
pre = sorted(set(li_l["ids"]["print_prefixes"]) | set(li_u["ids"]["print_prefixes"]))
if pre != li_l["ids"]["print_prefixes"]:
    li_l["ids"]["print_prefixes"] = pre
    changed.append("limits.ids.print_prefixes")

# messages.json
me_l, me_u = load(LOCAL / "messages.json"), load(SRC / "messages.json")
for k, v in me_u["messages"].items():
    if k not in me_l["messages"]:
        me_l["messages"][k] = v
        changed.append(f"messages.{k}")

if not changed:
    print("CHANGED nothing (already applied)")
    sys.exit(0)
print("CHANGED " + ", ".join(changed))
if CHECK:
    print("CHECK only: nothing written")
    sys.exit(0)
dump(LOCAL / "stage_plan.json", sp_l)
dump(LOCAL / "limits.json", li_l)
dump(LOCAL / "messages.json", me_l)
print("WROTE stage_plan.json, limits.json, messages.json")
