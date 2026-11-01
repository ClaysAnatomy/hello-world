"""taste_bridge: turn after-play ratings into seed weights.

Project decision (Entry 024): there is no separate feedback_ingest.py; the
existing taste layer (store.py, learn.py) owns feedback. This module is the
pure function those files call, plus a thin command line for testing:

    python authoring_kit\\python\\taste_bridge.py --ws <case folder> --answers <answers.json> --root .

answers.json holds IDs and integers only, for example
    {"answers": {"FB-01": 4, "FB-02": 5}, "numbers": {"FB-N1": 95}}
The weights file (taste_profile in kit_config.json) is what seed_sampler reads.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402

TARGET_KEYS = {"patterns", "mechanism", "red_herring", "stakes", "human_question", "irony",
               "setting_texture", "name_pool"}


def validate_answers(answers: dict, form: dict) -> list[str]:
    """Return check IDs for problems; empty when valid. Text is never accepted."""
    bad: list[str] = []
    if not isinstance(answers, dict) or set(answers) - {"answers", "numbers"}:
        return ["FB-00"]
    qs = {q["id"]: q for q in form["questions"]}
    lo, hi = form["scale"]["min"], form["scale"]["max"]
    for qid, val in answers.get("answers", {}).items():
        if qid not in qs or not isinstance(val, int) or isinstance(val, bool) or not lo <= val <= hi:
            bad.append(qid if qid in qs else "FB-00")
    nums = {n["id"]: n for n in form.get("extra_numbers", [])}
    for nid, val in answers.get("numbers", {}).items():
        n = nums.get(nid)
        if n is None or not isinstance(val, int) or isinstance(val, bool) or not n["min"] <= val <= n["max"]:
            bad.append(nid if n else "FB-00")
    return bad


def apply(profile: dict, answers: dict, seeds: dict, form: dict | None = None,
          limits: dict | None = None) -> dict:
    """Return a new profile with weights nudged by the answers."""
    form = form or K.data("feedback_form")
    lim = (limits or K.data("limits"))["taste"]
    lo, hi = form["scale"]["min"], form["scale"]["max"]
    mid = (lo + hi) / 2.0
    weights = dict(profile.get("weights", {}))
    qs = {q["id"]: q for q in form["questions"]}
    for qid, val in sorted(answers.get("answers", {}).items()):
        q = qs[qid]
        if q.get("kind") == "difficulty":
            continue
        delta = lim["learning_rate"] * (val - mid) / (hi - mid)
        for key in q["targets"]:
            if key not in TARGET_KEYS:
                continue
            ids = seeds.get(key, [])
            for sid in (ids if isinstance(ids, list) else [ids]):
                w = weights.get(sid, 1.0) * (1.0 + delta)
                weights[sid] = round(min(max(w, lim["min_weight"]), lim["max_weight"]), 4)
    return {"version": 1, "cases": int(profile.get("cases", 0)) + 1, "weights": dict(sorted(weights.items()))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", required=True)
    ap.add_argument("--answers", required=True)
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    out = K.Out()
    form = K.data("feedback_form")
    try:
        answers = K.load_json(args.answers)
        seeds = K.load_json(Path(args.ws) / "checkpoints" / "seeds.json")
    except (OSError, ValueError):
        out.say("TASTE_BAD", "FB-00")
        return 2
    bad = validate_answers(answers, form)
    if bad:
        for b in bad:
            out.say("TASTE_BAD", b)
        return 1
    cfg = K.data("kit_config")
    path = Path(args.root) / cfg["state"]["taste_profile"]
    profile = K.load_json(path) if path.is_file() else {}
    K.dump_json(apply(profile, answers, seeds, form), path)
    out.say("TASTE_OK", len(answers.get("answers", {})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
