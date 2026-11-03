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
pause_flag = src_root / f"_pause_{unit}"
if pause_flag.is_file():
    pause_flag.unlink()
    print("Claude AI usage limit reached|1767225600")
    sys.exit(1)
src = src_root / unit
if src.is_dir():
    for p in src.rglob("*"):
        if p.is_file():
            dst = here / p.relative_to(src)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dst)
raw = src_root / f"_raw_{unit}"
if raw.is_dir():  # files written byte for byte (cut-off or BOM cases)
    for p in raw.rglob("*"):
        if p.is_file():
            dst = here / p.relative_to(raw)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(p.read_bytes())
result = src_root / f"_result_{unit}"
subtype = result.read_text(encoding="utf-8").strip() if result.is_file() else "success"
print(f"stderr story {CANARY}", file=sys.stderr)
print(json.dumps({"num_turns": 2, "total_cost_usd": 0.01, "subtype": subtype, "duration_ms": 1234,
                  "permission_denials": [{"tool": CANARY}] if subtype == "denied" else [],
                  "result": f"Here is the story: {CANARY}"}))
sys.exit(0 if subtype in ("success", "denied") else 1)
