"""compat_check: read the real engine schema, vocabulary, rules and contract,
and report which aha patterns the engine can express.

Usage (PowerShell, from the project root):
    python authoring_kit\\python\\compat_check.py --root . [--out <file>]

Prints only pattern IDs, AVAILABLE or UNAVAILABLE, the missing engine term,
and counts. Exit 0 when at least one pattern is available, 1 when none,
2 on a setup error.
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402


def _glob_many(root: Path, patterns: list[str]) -> list[Path]:
    found: list[Path] = []
    for pat in patterns:
        for p in sorted(glob.glob(str(root / pat))):
            pp = Path(p)
            if pp.is_file() and pp not in found:
                found.append(pp)
    return found


def _collect(obj, keys: set[str], values: set[str]) -> None:
    for k in K.walk_keys(obj):
        keys.add(k)
    for _, v in K.walk_leaves(obj):
        if isinstance(v, str) and len(v) <= 64:
            values.add(v)


def _rule_entries(obj, id_keys, text_keys):
    items = obj if isinstance(obj, list) else [obj]
    for it in items:
        if isinstance(it, dict):
            rid = next((it[k] for k in id_keys if isinstance(it.get(k), str)), None)
            text = next((it[k] for k in text_keys if isinstance(it.get(k), str)), None)
            yield rid, text


def run_compat(root: Path, cfg: dict | None = None, capmap: dict | None = None,
               patterns: dict | None = None) -> dict:
    cfg = cfg or K.data("kit_config")
    capmap = capmap or K.data("capability_map")
    patterns = patterns or K.data("patterns")
    eng = cfg["engine"]
    report: dict = {"errors": [], "warnings": [], "engine_files": {}}

    schema_files = _glob_many(root, eng["case_schema_globs"])
    if not schema_files:
        report["errors"].append("KT-CP-01")
        return report
    skin_files = _glob_many(root, eng.get("skin_schema_globs", []))
    vocab_files = _glob_many(root, eng.get("vocabulary_globs", []))
    if not vocab_files:
        report["warnings"].append("KT-CP-02")
    contract = root / eng["contract_json"] if eng.get("contract_json") else None
    contract_files = [contract] if contract and contract.is_file() else []
    if not contract_files:
        report["warnings"].append("KT-CP-03")

    keys: set[str] = set()
    values: set[str] = set()
    property_names: set[str] = set()
    for f in schema_files + skin_files:
        obj = K.load_json(f)
        _collect(obj, keys, values)
        stack = [obj]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                if isinstance(cur.get("properties"), dict):
                    property_names.update(cur["properties"].keys())
                stack.extend(cur.values())
            elif isinstance(cur, list):
                stack.extend(cur)
    for f in vocab_files + contract_files:
        _collect(K.load_json(f), keys, values)
    for f in schema_files + skin_files + vocab_files + contract_files:
        report["engine_files"][f.relative_to(root).as_posix()] = K.sha256_file(f)

    rule_ids: list[str] = []
    rule_texts: dict[str, str] = {}
    for f in sorted(glob.glob(str(root / eng["rules_glob"]))):
        try:
            obj = K.load_json(f)
        except Exception:
            report["warnings"].append("KT-CP-04")
            continue
        got = False
        for rid, text in _rule_entries(obj, eng.get("rule_id_keys", ["id"]), eng.get("rule_text_keys", [])):
            if rid:
                got = True
                if rid not in rule_ids:
                    rule_ids.append(rid)
                if text:
                    rule_texts[rid] = text
        if not got:
            stem = Path(f).stem
            if stem not in rule_ids:
                rule_ids.append(stem)

    lower_index: dict[str, str] = {}
    for t in sorted(keys | values):
        lower_index.setdefault(t.lower(), t)

    resolved: dict[str, str | None] = {}
    for cap in capmap["capabilities"]:
        hit = None
        for cand in cap["candidates"]:
            if cand.lower() in lower_index:
                hit = lower_index[cand.lower()]
                break
        resolved[cap["id"]] = hit

    pat_report: dict[str, dict] = {}
    for pat in patterns["patterns"]:
        missing: list[str] = []
        generic = False
        for item in pat["requires"]:
            alts = item if isinstance(item, list) else [item]
            hit = next((a for a in alts if resolved.get(a)), None)
            if hit is None:
                missing.append(alts[0])
            elif hit != alts[0]:
                generic = True
        pat_report[pat["id"]] = {"available": not missing, "missing": missing,
                                 "mode": "GENERIC" if generic else "NATIVE"}

    suffixes = tuple(capmap.get("prose_field_hints", {}).get("suffixes", []))
    prose_count = sum(1 for p in property_names if suffixes and p.endswith(suffixes))

    report.update({
        "capabilities": resolved,
        "patterns": pat_report,
        "rule_ids": rule_ids,
        "rule_texts": rule_texts,
        "property_names": sorted(property_names),
        "prose_field_count": prose_count,
        "available_count": sum(1 for v in pat_report.values() if v["available"]),
    })
    return report


def first_candidate(capmap: dict, cap_id: str) -> str:
    for cap in capmap["capabilities"]:
        if cap["id"] == cap_id:
            return cap["candidates"][0]
    return cap_id


def print_report(report: dict, out: K.Out, capmap: dict | None = None) -> int:
    capmap = capmap or K.data("capability_map")
    if report.get("errors"):
        for e in report["errors"]:
            out.say("COMPAT_ERROR", e)
        return 2
    for w in report.get("warnings", []):
        out.say("COMPAT_WARN", w)
    out.trust(terms=[c for cap in capmap["capabilities"] for c in cap["candidates"]] + ["NATIVE", "GENERIC"])
    for pid, info in report["patterns"].items():
        if info["available"]:
            out.say("COMPAT_AVAILABLE", pid, info.get("mode", "NATIVE"))
        else:
            out.say("COMPAT_UNAVAILABLE", pid, first_candidate(capmap, info["missing"][0]))
    total = len(report["patterns"])
    out.say("COMPAT_SUMMARY", report["available_count"], total)
    out.say("COMPAT_RULES", len(report["rule_ids"]))
    out.say("COMPAT_PROSE_FIELDS", report["prose_field_count"])
    return 0 if report["available_count"] > 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    out = K.Out()
    root = Path(args.root).resolve()
    try:
        report = run_compat(root)
    except K.KitError as e:
        out.say(e.msg_id, *e.args_out)
        return e.code
    code = print_report(report, out)
    if args.out and code != 2:
        K.dump_json(report, Path(args.out))
        out.say("COMPAT_WRITTEN")
    return code


if __name__ == "__main__":
    sys.exit(main())
