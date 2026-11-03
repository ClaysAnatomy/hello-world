"""placeholder_probe: find which engine rules fail only because prose is still a placeholder.

S2 writes the engine case with a placeholder in every player-facing prose field.
Some real rules may need real prose (search findability, for example). This
probe copies a passing fixture, replaces its prose with placeholder tokens, runs
the engine checks that run at S2 on both copies, and reports the rules that fail
only on the placeholder copy. Those are the rules to list in limits.json under
tolerated_engine_rules. No model call; nothing outside a temporary folder is
written unless --write is given.

PowerShell, from the project root:
    python authoring_kit\\python\\placeholder_probe.py --root . --case engine\\fixtures\\CASE-FIX-03\\case.json --skin engine\\fixtures\\skins\\SKIN-FIX_A.json [--write]
"""
from __future__ import annotations

import argparse
import copy
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402
from compat_check import run_compat  # noqa: E402
from repair_builder import error_ids, parse_engine_output  # noqa: E402
from runners import run_engine_check  # noqa: E402


def prose_key(key: str, suffixes: tuple[str, ...], exact: set[str]) -> bool:
    return key in exact or (bool(suffixes) and key.endswith(suffixes))


def placeholderise(obj, suffixes: tuple[str, ...], exact: set[str], counter: list[int]):
    """Replace prose strings in place with PP-PROBE-n tokens. Returns obj."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if prose_key(k, suffixes, exact):
                if isinstance(v, str) and v:
                    counter[0] += 1
                    obj[k] = f"PP-PROBE-{counter[0]}"
                    continue
                if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
                    for i in range(len(v)):
                        counter[0] += 1
                        v[i] = f"PP-PROBE-{counter[0]}"
                    continue
            placeholderise(v, suffixes, exact, counter)
    elif isinstance(obj, list):
        for v in obj:
            placeholderise(v, suffixes, exact, counter)
    return obj


def failing(root: Path, cfg: dict, case: Path, skin: Path, ws: Path, rule_ids: list[str]) -> set[str]:
    out: set[str] = set()
    for chk in cfg["engine_checks"]:
        if chk.get("enabled") and "S2" in chk["at"]:
            code, text = run_engine_check(root, cfg, chk, case, skin, ws, int(K.data("limits")["timeouts"]["engine_check_seconds"]))
            out |= set(error_ids(parse_engine_output(text, code, chk["id"], rule_ids)))
    return out


def run_probe(root: Path, case_path: Path, skin_path: Path) -> dict:
    cfg = K.data("kit_config")
    capmap = K.data("capability_map")
    suffixes = tuple(capmap.get("prose_field_hints", {}).get("suffixes", []))
    exact = set(cfg.get("probe", {}).get("exact_keys", []))
    compat = run_compat(root)
    if compat.get("errors"):
        raise K.KitError("COMPAT_ERROR", compat["errors"][0], code=2)
    rule_ids = compat["rule_ids"]
    tmp = Path(tempfile.mkdtemp(prefix="mm_kit_probe_"))
    try:
        original = K.load_json(case_path)
        counter = [0]
        probed = placeholderise(copy.deepcopy(original), suffixes, exact, counter)
        K.dump_json(original, tmp / "original.json")
        K.dump_json(probed, tmp / "probed.json")
        base = failing(root, cfg, tmp / "original.json", skin_path, tmp, rule_ids)
        with_ph = failing(root, cfg, tmp / "probed.json", skin_path, tmp, rule_ids)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return {"replaced": counter[0], "base_failures": sorted(base),
            "placeholder_only": sorted(with_ph - base), "rule_ids": rule_ids}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--case", required=True)
    ap.add_argument("--skin", required=True)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    out = K.Out()
    root = Path(args.root).resolve()
    try:
        rep = run_probe(root, Path(args.case).resolve(), Path(args.skin).resolve())
    except K.KitError as e:
        out.say(e.msg_id, *e.args_out)
        return e.code
    out.trust(terms=rep["rule_ids"])
    out.say("PROBE_COUNT", rep["replaced"])
    for rid in rep["base_failures"]:
        out.say("PROBE_BASE", rid)
    for rid in rep["placeholder_only"]:
        out.say("PROBE_RULE", rid)
    if not rep["placeholder_only"]:
        out.say("PROBE_NONE")
    if args.write:
        lim_path = K.DATA_DIR / "limits.json"
        lim = K.load_json(lim_path)
        lim["tolerated_engine_rules"]["S2"] = rep["placeholder_only"]
        lim["tolerated_engine_rules"]["S3_GATE"] = rep["placeholder_only"]
        K.dump_json(lim, lim_path)
        out.say("PROBE_WRITTEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
