"""voice_lint: deterministic prose checks on S3 and S4 fills.

Ban lists, word limits, exact-string preservation, findings and assessment
separation, per-voice rules, claims within assignment, option length
normalisation, distractor entity references, name drift, dash density and
repeated-phrase overlap across documents. Findings carry check IDs and
placeholder tokens only.
"""
from __future__ import annotations

import re
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402
from case_checks import ERROR, WARN, F  # noqa: E402


def _cats():
    return K.data("ban_lists")["categories"]


def _names(bible: dict) -> tuple[set[str], set[str]]:
    full, parts = set(), set()
    for c in bible["cast"]:
        g, f = c["name"]["given"], c["name"]["family"]
        full.add(f"{g} {f}")
        parts.update([g, f])
    return full, parts


def _entities(bible: dict) -> list[str]:
    _, parts = _names(bible)
    return sorted(parts | {l["name"] for l in bible["locations"]})


def _voice_for(owner: str, plan: dict) -> dict | None:
    clue = next((c for c in plan["clues"] if c["id"] == owner), None)
    if not clue or not clue.get("dept"):
        return None
    dept = next((d for d in plan["departments"] if d["id"] == clue["dept"]), None)
    if not dept:
        return None
    return next((p for p in K.data("voice_matrix")["profiles"] if p["id"] == dept["voice_id"]), None)


def _ban_scan(text: str, token: str, applies: tuple[str, ...]) -> list[dict]:
    low = text.lower()
    out = []
    for cat in _cats():
        if cat["applies_to"] not in applies:
            continue
        if cat["id"].startswith("BL-NAMES"):
            continue
        if any(K.phrase_in(low, t) for t in cat["terms"]):
            out.append(F(cat["check"], token, cat["severity"]))
    return out


def _stock_names(text: str, token: str, bible: dict) -> list[dict]:
    full, parts = _names(bible)
    allowed = {p.lower() for p in parts}
    low = text.lower()
    for cat in _cats():
        if not cat["id"].startswith("BL-NAMES"):
            continue
        for t in cat["terms"]:
            if t.lower() in allowed:
                continue
            if K.phrase_in(low, t):
                return [F("VL-02", token, cat["severity"])]
    return []


def _voice_rules(text: str, token: str, profile: dict) -> list[dict]:
    vm = K.data("voice_matrix")["lexicons"]
    rules = profile["rules"]
    out = []
    sents = K.sentences(text)
    if sents:
        avg = sum(len(K.words(s)) for s in sents) / len(sents)
        lo, hi = rules["assessment_sentence_words"]
        if avg < lo or avg > hi:
            out.append(F("VL-08", token))
    ws = K.words(text)
    singular = any(w in vm["first_person_singular"] for w in ws)
    plural = any(w in vm["first_person_plural"] for w in ws)
    fp = rules["first_person"]
    if fp == "forbidden" and (singular or plural):
        out.append(F("VL-08", token))
    if fp == "plural_only" and singular:
        out.append(F("VL-08", token))
    low = text.lower()
    hedged = any(K.phrase_in(low, h) for h in vm["hedges"])
    if rules["hedges"] == "forbidden" and hedged:
        out.append(F("VL-08", token))
    if rules["hedges"] == "required" and not hedged:
        out.append(F("VL-08", token))
    if rules.get("digits_required") and not re.search(r"[0-9]", text):
        out.append(F("VL-08", token))
    if any(K.phrase_in(low, t) for t in rules.get("forbidden_any", [])):
        out.append(F("VL-08", token))
    need = rules.get("required_in_assessment_any", [])
    if need and not any(t in low if not t[0].isalnum() else K.phrase_in(low, t) for t in need):
        out.append(F("VL-17", token, WARN))
    return out


def _name_drift(text: str, token: str, bible: dict) -> list[dict]:
    lim = K.data("limits")["prose"]
    _, parts = _names(bible)
    names = {p.lower() for p in parts}
    out = []
    for w in re.findall(r"\b[A-Z][a-zA-Z']+\b", text):
        lw = w.lower()
        if len(lw) < lim["name_drift_min_length"] or lw in names:
            continue
        for n in names:
            if len(n) >= lim["name_drift_min_length"]:
                d = K.levenshtein(lw, n, cap=lim["name_drift_max_distance"])
                if 0 < d <= lim["name_drift_max_distance"]:
                    return [F("VL-16", token)]
    return out


def _density(text: str, token: str) -> list[dict]:
    dens = K.data("ban_lists")["density"]
    n = max(len(K.words(text)), 1)
    dashes = text.count("—") + text.count(" -- ") + text.count("– ")
    out = []
    if dashes * 100.0 / n > dens["em_dash_per_100_words_warn"]:
        out.append(F("VL-15", token, WARN))
    if len(re.findall(dens["not_just_but_pattern"], text.lower())) > dens["not_just_but_max"]:
        out.append(F("VL-15", token, WARN))
    return out


def lint_fill(fill: dict, owner: str, plan: dict, bible: dict) -> list[dict]:
    lim = K.data("limits")
    errs = K.schema_errors(fill, K.schema("fill"))
    if errs:
        return [F("KT-FL-01", p) for p in errs[:20]]
    phs = {ph["token"]: ph for ph in plan["placeholders"] if ph["owner"] == owner}
    out: list[dict] = []
    if fill["owner"] != owner or set(fill["fills"]) != set(phs) or not set(fill["claims"]) <= set(phs):
        out.append(F("KT-FL-01", "$"))
        return out
    find_rx = K.placeholder_search_regex(lim["ids"]["placeholder_format"])
    crit = {c["id"]: c["value"] for c in bible["critical_strings"]}
    vm = K.data("voice_matrix")["lexicons"]
    profile = _voice_for(owner, plan)

    for tok, text in fill["fills"].items():
        ph = phs[tok]
        if find_rx.search(text):
            out.append(F("KT-FL-01", tok))
        n = len(K.words(text))
        if n == 0 or n > ph.get("max_words", lim["prose"]["default_max_words"]):
            out.append(F("VL-12", tok))
        out += _ban_scan(text, tok, ("fills", "fills_and_bible"))
        out += _stock_names(text, tok, bible)
        for cs in ph["required_strings"]:
            if crit.get(cs) is None or crit[cs] not in text:
                out.append(F("VL-06", tok))
        low = text.lower()
        if ph["kind"] == "finding" and any(K.phrase_in(low, m) for m in vm["assessment_markers"]):
            out.append(F("VL-07", tok))
        if ph["kind"] == "assessment" and profile:
            out += _voice_rules(text, tok, profile)
        claims = set(fill["claims"].get(tok, []))
        if not claims <= set(ph["facts"]):
            out.append(F("VL-11", tok))
        elif claims != set(ph["facts"]):
            out.append(F("VL-11", tok, WARN))
        out += _name_drift(text, tok, bible)
        out += _density(text, tok)

    out += lint_options(fill, phs, bible)
    # de-duplicate
    seen, uniq = set(), []
    for f in out:
        key = (f["id"], f["path"], f["sev"])
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq


def lint_options(fill: dict, phs: dict, bible: dict) -> list[dict]:
    tol = K.data("limits")["prose"]["option_length_tolerance"]
    correct = {o["id"]: o["correct"] for q in bible["questions"] for o in q["options"]}
    ents = [e.lower() for e in _entities(bible)]
    groups: dict[str, list[tuple[str, str]]] = {}
    out = []
    for tok, ph in phs.items():
        if ph["kind"] == "option" and ph.get("question"):
            groups.setdefault(ph["question"], []).append((tok, fill["fills"].get(tok, "")))
            if correct.get(ph.get("option")) is False:
                low = fill["fills"].get(tok, "").lower()
                if not any(K.phrase_in(low, e) for e in ents):
                    out.append(F("VL-05", tok))
    for q, items in groups.items():
        lengths = [len(t.strip()) for _, t in items]
        if len(lengths) < 2:
            continue
        mean = sum(lengths) / len(lengths)
        for (tok, _), ln in zip(items, lengths):
            if mean and abs(ln - mean) / mean > tol + 1e-9:
                out.append(F("VL-04", tok))
    return out


def shingles(text: str, n: int) -> set[tuple[str, ...]]:
    ws = K.words(text)
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def lint_overlap(fills_by_owner: dict[str, dict], order: list[str]) -> list[dict]:
    """VL-09 across owners. The later owner in reading order is blamed."""
    lim = K.data("limits")["prose"]
    n = lim["ngram_n"]
    sev = lim.get("overlap_severity", ERROR)
    sh = {o: set().union(*[shingles(t, n) for t in f["fills"].values()]) if f["fills"] else set()
          for o, f in fills_by_owner.items()}
    pos = {o: i for i, o in enumerate(order)}
    out, blamed = [], set()
    for a, b in combinations(sorted(sh, key=lambda o: pos.get(o, 999)), 2):
        if len(sh[a] & sh[b]) > lim["max_shared_ngrams_between_owners"] and b not in blamed:
            out.append(F("VL-09", b, sev))
            blamed.add(b)
    return out


def lint_bible_names(bible: dict) -> list[dict]:
    """VL-02 on the bible: soft warning when stock names appear anywhere."""
    blob = " ".join(K.string_leaves(bible))
    return _stock_names(blob, "$", bible)
