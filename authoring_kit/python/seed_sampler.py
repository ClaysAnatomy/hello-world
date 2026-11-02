"""seed_sampler: choose a run's seeds before any model call.

Picks 1 or 2 aha patterns from the AVAILABLE set, a mechanism, a red-herring
type, stakes, a human question, an irony, a setting texture, a name pool and
cast names with distinct initials and sounds, critical strings, counts and a
department voice mix. Choices are weighted by the taste profile and pushed
away from anything in the ledger's recent window. Deterministic for a given
integer seed. Prints nothing about what it chose.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402
from ledger import Ledger  # noqa: E402


def _weight(kind: str, item_id: str, taste: dict, ledger: Ledger, lim: dict) -> float:
    w = float(taste.get("weights", {}).get(item_id, 1.0))
    if ledger.recent(kind, item_id, lim["ledger"]["window"]):
        w *= lim["ledger"]["novelty_penalty"]
    return max(w, 0.0001)


def _pick(rng: random.Random, kind: str, items: list[dict], taste: dict, ledger: Ledger, lim: dict) -> dict:
    weights = [_weight(kind, it["id"], taste, ledger, lim) for it in items]
    return rng.choices(items, weights=weights, k=1)[0]


def _sound_key(name: str) -> str:
    n = name.lower()
    n = n.replace("ph", "f").replace("ck", "k").replace("qu", "k")
    n = n.translate(str.maketrans("cqzwj", "ksswy"))
    cons = [ch for ch in n if ch.isalpha() and ch not in "aeiouy"]
    return "".join(cons[:2])


def _pick_names(rng: random.Random, pool: dict, count: int, ledger: Ledger, lim: dict,
                banned: set[str]) -> list[dict]:
    given = [g for g in pool["given"] if g.lower() not in banned]
    family = [f for f in pool["family"] if f.lower() not in banned]
    rng.shuffle(given)
    rng.shuffle(family)
    window = lim["ledger"]["window"]
    given.sort(key=lambda g: ledger.recent("given", g, window))
    family.sort(key=lambda f: ledger.recent("family", f, window))

    def choose(names: list[str]) -> list[str]:
        out: list[str] = []
        initials, endings, sounds = set(), set(), set()
        for nm in names:
            if nm[0] in initials or nm[-2:].lower() in endings or _sound_key(nm) in sounds:
                continue
            out.append(nm)
            initials.add(nm[0])
            endings.add(nm[-2:].lower())
            sounds.add(_sound_key(nm))
            if len(out) == count:
                break
        return out

    g = choose(given)
    f = choose(family)
    if len(g) < count or len(f) < count:
        raise K.KitError("ERR_NAME_POOL", pool["id"], count)
    # given and family initials must not echo each other within one person
    people = []
    for i in range(count):
        people.append({"slot": f"N{i + 1}", "given": g[i], "family": f[i]})
    return people


def _times(rng: random.Random, n: int) -> list[str]:
    out: list[str] = []
    while len(out) < n:
        hh = rng.randint(6, 23)
        mm = rng.randint(0, 59)
        if mm % 5 == 0:
            continue
        cand = f"{hh:02d}:{mm:02d}"
        if cand in out:
            continue
        if out:
            a = int(out[0][:2]) * 60 + int(out[0][3:])
            b = hh * 60 + mm
            if abs(a - b) < 7 or len(set(cand) & set(out[0])) > 3:
                continue
        out.append(cand)
    return out


def _code(rng: random.Random) -> str:
    letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
    while True:
        digits = "".join(str(rng.randint(0, 9)) for _ in range(4))
        if len(set(digits)) >= 3:
            return f"{rng.choice(letters)}-{digits}"


def sample(rng_seed: int, compat: dict, ledger: Ledger | None = None, taste: dict | None = None) -> dict:
    ledger = ledger or Ledger(None)
    taste = taste or {}
    lim = K.data("limits")
    pats = K.data("patterns")["patterns"]
    seeds_data = K.data("story_seeds")
    voices = K.data("voice_matrix")["profiles"]
    bans = K.data("ban_lists")
    banned = set()
    for cat in bans["categories"]:
        if cat["id"] in ("BL-NAMES-GIVEN", "BL-NAMES-FAMILY"):
            banned.update(t.lower() for t in cat["terms"])

    rng = random.Random(rng_seed)
    available = [p for p in pats if compat.get("patterns", {}).get(p["id"], {}).get("available")]
    if not available:
        raise K.KitError("ERR_NO_PATTERNS", code=1)

    first = _pick(rng, "pattern", available, taste, ledger, lim)
    chosen = [first["id"]]
    if lim["budget"]["max_patterns"] >= 2 and rng.random() < 0.5:
        partners = [p for p in available
                    if p["id"] in first.get("combines_with", [])
                    and first["id"] not in p.get("conflicts_with", [])
                    and p["id"] not in first.get("conflicts_with", [])]
        if partners:
            chosen.append(_pick(rng, "pattern", partners, taste, ledger, lim)["id"])

    b = lim["budget"]
    suspects = rng.randint(b["min_suspects"], b["max_suspects"])
    others = rng.randint(1, 2)
    cast_total = min(suspects + 1 + others, b["max_cast_total"])
    pool = _pick(rng, "name_pool", seeds_data["name_pools"], taste, ledger, lim)
    names = _pick_names(rng, pool, cast_total, ledger, lim, banned)

    n_crit = b["max_critical_strings"]
    kinds = ["CSK-TIME"] + [rng.choice(["CSK-TIME", "CSK-CODE"]) for _ in range(n_crit - 1)]
    times = _times(rng, kinds.count("CSK-TIME"))
    crit = []
    ti = 0
    for i, kind in enumerate(kinds):
        if kind == "CSK-TIME":
            value = times[ti]
            ti += 1
        else:
            value = _code(rng)
        crit.append({"id": f"CS-{i + 1}", "kind": kind, "value": value})

    mix = [v["id"] for v in voices]
    rng.shuffle(mix)

    seeds = {
        "seed": rng_seed,
        "patterns": chosen,
        "mechanism": _pick(rng, "mechanism", seeds_data["mechanisms"], taste, ledger, lim)["id"],
        "red_herring": _pick(rng, "red_herring", seeds_data["red_herrings"], taste, ledger, lim)["id"],
        "stakes": _pick(rng, "stakes", seeds_data["stakes"], taste, ledger, lim)["id"],
        "human_question": _pick(rng, "human_question", seeds_data["human_questions"], taste, ledger, lim)["id"],
        "irony": _pick(rng, "irony", seeds_data["ironies"], taste, ledger, lim)["id"],
        "setting_texture": _pick(rng, "setting_texture", seeds_data["setting_textures"], taste, ledger, lim)["id"],
        "name_pool": pool["id"],
        "suspect_count": suspects,
        "cast_total": cast_total,
        "location_count": rng.randint(2, b["max_locations"]),
        "cast_names": names,
        "critical_strings": crit,
        "dept_mix": mix[: b["max_departments"]],
    }
    # picked last so adding it left every earlier choice for a given seed unchanged
    seeds["lens_hint"] = _pick(rng, "lens_hint", K.data("trope_lenses")["lenses"], taste, ledger, lim)["id"]
    return seeds
