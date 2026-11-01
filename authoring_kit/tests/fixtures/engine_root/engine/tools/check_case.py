"""NONSENSE fake of engine/tools/check_case.py for kit tests.
Prints only rule IDs, JSON paths and PASS/FAIL, like the real tool."""
import json, sys
case = json.load(open(sys.argv[1], encoding="utf-8"))
def leaves(o, path="$"):
    if isinstance(o, dict):
        for k, v in o.items(): yield from leaves(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from leaves(v, f"{path}[{i}]")
    else: yield path, o
bad = 0
print("FP-01 PASS")
hit = [p for p, v in leaves(case) if isinstance(v, str) and "FORCE-FAIL-FP02" in v]
if hit: print(f"FP-02 FAIL {hit[0]}"); bad += 1
else: print("FP-02 PASS")
short = [i for i, c in enumerate(case.get("clues", [])) if len(str(c.get("raw_observation_text", "x y")).split()) < 2]
if short: print(f"FP-03 FAIL $.clues[{short[0]}].raw_observation_text"); bad += 1
else: print("FP-03 PASS")
empty = [i for i, c in enumerate(case.get("clues", [])) if not c.get("record_title")]
if empty: print(f"DK-01 FAIL $.clues[{empty[0]}].record_title"); bad += 1
else: print("DK-01 PASS")
sys.exit(1 if bad else 0)
