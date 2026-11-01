"""runners: start child processes for Mode A agents and for engine checks.

Agent stdout and stderr are never written anywhere. They are held in memory
only to (a) read whitelisted numeric usage fields when configured and (b)
test, case-insensitively, for the configured usage-limit patterns, so a run
can pause instead of failing. Engine output is held in memory long enough to
extract rule IDs and paths.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402


def _fill(argv: list[str], tokens: dict[str, str]) -> list[str]:
    """Fill {token}s. An argument whose token fills to an empty value is dropped whole,
    so write optional flags as one argument, for example "--model={model}"."""
    out = []
    for a in argv:
        if any("{" + k + "}" in a and v == "" for k, v in tokens.items()):
            continue
        for k, v in tokens.items():
            a = a.replace("{" + k + "}", v)
        out.append(a)
    return out


def stage_model(stage: str, agent_cfg: dict) -> tuple[str, str]:
    """Model and effort for a stage: stage_plan values, else the agent defaults."""
    plan = K.data("stage_plan")
    entry = plan["repair"] if stage == "S5" else next((s for s in plan["stages"] if s["id"] == stage), {})
    model = entry.get("model") or agent_cfg.get("default_model") or ""
    effort = entry.get("effort") or agent_cfg.get("default_effort") or ""
    return model, effort


def run_agent(cfg: dict, stage_dir: Path, prompt_file: Path, max_turns: int,
              timeout_s: int, stage: str = "", agent_key: str = "agent") -> tuple[int, dict, bool]:
    """Run one agent invocation. Returns (exit code, numeric usage, paused)."""
    ag = cfg[agent_key]
    if not ag.get("argv"):
        raise K.KitError("ERR_NO_AGENT", code=2)
    model, effort = stage_model(stage, ag)
    argv = _fill(ag["argv"], {
        "prompt_file": str(prompt_file),
        "stage_dir": str(stage_dir),
        "max_turns": str(max_turns),
        "model": model,
        "effort": effort,
        "python": K.resolve_python(cfg),
    })
    stdin_data = prompt_file.read_text(encoding="utf-8") if ag.get("stdin") == "prompt" else None
    try:
        proc = subprocess.run(argv, cwd=str(stage_dir), input=stdin_data, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout_s, env=K.child_env(cfg, agent_key))
    except subprocess.TimeoutExpired:
        return 124, {}, False
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
    pause_cfg = cfg.get("agent", {}).get("pause", {})
    blob = (proc.stdout + "\n" + proc.stderr).lower()
    paused = (proc.returncode in pause_cfg.get("exit_codes", [])
              or any(p.lower() in blob for p in pause_cfg.get("output_patterns", [])))
    code = proc.returncode
    del proc, blob  # all text output is dropped here
    return code, usage, paused


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
