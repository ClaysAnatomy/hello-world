"""Fake agent for kit tests. NONSENSE only.

Reads unit.json in its working folder, copies canned outputs from
$FAKE_AGENT_DIR/<unit>/ into the folder, records whether any *_API_KEY or
*_AUTH_TOKEN variable reached it, and prints a canary to stdout and stderr
(the kit must drop both).
"""
import json
import os
import shutil
import sys
from pathlib import Path

CANARY = "marmalade lighthouse quorum"

here = Path.cwd()
unit = json.loads((here / "unit.json").read_text(encoding="utf-8"))["unit"]
src_root = Path(os.environ["FAKE_AGENT_DIR"])
stdin_text = sys.stdin.read() if not sys.stdin.isatty() else ""
leaked = sorted(k for k in os.environ if k.upper().endswith(("_API_KEY", "_AUTH_TOKEN")))
log = src_root / "_calls.json"
calls = json.loads(log.read_text(encoding="utf-8")) if log.is_file() else []
calls.append({"unit": unit, "secret_vars": leaked, "stdin_chars": len(stdin_text), "argv": sys.argv[1:]})
log.write_text(json.dumps(calls), encoding="utf-8")
src = src_root / unit
if src.is_dir():
    for p in src.iterdir():
        shutil.copyfile(p, here / p.name)
print(f"stderr story {CANARY}", file=sys.stderr)
print(json.dumps({"num_turns": 2, "total_cost_usd": 0.01, "result": f"Here is the story: {CANARY}"}))
sys.exit(0)
