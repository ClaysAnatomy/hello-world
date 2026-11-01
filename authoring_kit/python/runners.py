"""runners: start child processes for Mode A agents and for engine checks.

Agent stdout and stderr are never written anywhere. If the config says the
agent prints a JSON usage report, only the configured numeric fields are kept.
Engine output is held in memory long enough to extract rule IDs and paths.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402


def _fill(argv: list[str], tokens: dict[str, str]) -> list[str]:
    out = []
    for a in argv:
        for k, v in tokens.items():
            a = a.replace("{" + k + "}", v)
        out.append(a)
    return out


def run_agent(cfg: dict, stage_dir: Path, prompt_file: Path, max_turns: int,
              timeout_s: int) -> tuple[int, dict]:
    ag = cfg["agent"]
    if not ag.get("argv"):
        raise K.KitError("ERR_NO_AGENT", code=2)
    argv = _fill(ag["argv"], {
        "prompt_file": str(prompt_file),
        "stage_dir": str(stage_dir),
        "max_turns": str(max_turns),
        "python": K.resolve_python(cfg),
    })
    stdin_data = prompt_file.read_text(encoding="utf-8") if ag.get("stdin") == "prompt" else None
    try:
        proc = subprocess.run(argv, cwd=str(stage_dir), input=stdin_data, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout_s, env=K.child_env(cfg))
    except subprocess.TimeoutExpired:
        return 124, {}
    except FileNotFoundError:
        raise K.KitError("ERR_AGENT_NOT_FOUND", code=2)
    usage: dict = {}
    if ag.get("usage_from_stdout_json"):
        try:
            obj = json.loads(proc.stdout)
            for name, key in ag.get("usage_keys", {}).items():
                val = obj.get(key) if isinstance(obj, dict) else None
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    usage[name] = val
        except (ValueError, TypeError):
            pass
    code = proc.returncode
    del proc  # all text output is dropped here
    return code, usage


def run_engine_check(root: Path, cfg: dict, check: dict, case: Path, skin: Path, ws: Path,
                     timeout_s: int) -> tuple[int, str]:
    argv = _fill(check["argv"], {
        "python": K.resolve_python(cfg), "case": str(case), "skin": str(skin), "ws": str(ws),
    })
    try:
        proc = subprocess.run(argv, cwd=str(root), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout_s,
                              env=K.child_env(cfg))
    except subprocess.TimeoutExpired:
        return 124, ""
    except FileNotFoundError:
        return 127, ""
    return proc.returncode, proc.stdout + "\n" + proc.stderr
