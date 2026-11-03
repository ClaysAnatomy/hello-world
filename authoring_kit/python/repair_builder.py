"""repair_builder: turn check results into a repair decision and a failures table.

The repair stage sees only check IDs, JSON paths or placeholder tokens, and the
fixed sentence describing each check. Raw engine output never reaches it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402
from case_checks import ERROR, F  # noqa: E402

REPAIR, ABORT_REPEAT, ABORT_CAP = "REPAIR", "ABORT_REPEAT", "ABORT_CAP"


def parse_engine_output(text: str, exit_code: int, check_id: str, rule_ids: list[str],
                        tolerated: list[str] | None = None) -> list[dict]:
    """Extract failing rule IDs and JSON paths from one engine tool's output."""
    cfg = K.data("kit_config")["engine_output"]
    path_rx = re.compile(cfg["path_regex"])
    fail_word = cfg["fail_word"]
    tolerated = set(tolerated or [])
    known = sorted(rule_ids, key=len, reverse=True)
    out: list[dict] = []
    unexplained = False
    only_tolerated = True
    for line in text.splitlines():
        if fail_word not in line:
            continue
        rid = next((r for r in known if re.search(r"(?<![A-Za-z0-9])" + re.escape(r) + r"(?![A-Za-z0-9])", line)), None)
        if rid is None:
            unexplained = True
            only_tolerated = False
            continue
        if rid in tolerated:
            continue
        only_tolerated = False
        m = path_rx.search(line)
        out.append(F(rid, m.group(0) if m else "$"))
    if exit_code != 0 and not out:
        saw_tolerated_only = only_tolerated and not unexplained and any(fail_word in ln for ln in text.splitlines())
        if not saw_tolerated_only:
            out.append(F(check_id, "$"))
    return out


def error_ids(findings: list[dict]) -> list[str]:
    return sorted({f["id"] for f in findings if f["sev"] == ERROR})


def decide(previous: dict | None, new_findings: list[dict], attempt_round: int) -> str:
    """Decide what follows a failed attempt.

    previous: the failure record before this attempt (None for an original attempt).
    attempt_round: 0 for the original stage, 1.. for repair rounds.
    """
    lim = K.data("limits")["repair"]
    new_ids = set(error_ids(new_findings))
    if attempt_round == 0 or previous is None:
        return REPAIR if lim["max_repair_rounds"] > 0 else ABORT_CAP
    if lim["abort_on_repeated_id"] and previous.get("history"):
        if set(previous["history"][-1]) & new_ids:
            return ABORT_REPEAT
    if attempt_round >= lim["max_repair_rounds"]:
        return ABORT_CAP
    return REPAIR


def failures_table(findings: list[dict], rule_texts: dict[str, str]) -> str:
    catalog = K.data("check_catalog")["checks"]
    rows = ["| Check | Where | Requirement |", "|---|---|---|"]
    for f in findings:
        if f["sev"] != ERROR:
            continue
        req = catalog.get(f["id"]) or rule_texts.get(f["id"]) or "Engine rule; see the authoring contract for this rule ID."
        where = f["path"]
        if f.get("file"):
            where = f["file"] + (f", line {f['line']} of {f.get('lines', '?')}" if f.get("line") else "") \
                + (f" ({f['path']})" if f["path"] != "$" else "")
        rows.append(f"| {f['id']} | {where} | {req} |")
    return "\n".join(rows)
