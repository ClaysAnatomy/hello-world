"""Mixed media: physical artifacts, calculated consistently.

A document in the plan may be dressed as a physical artifact (a photograph, an ID
badge scan, a newspaper page, a report form) by giving it a `media` declaration.
This module turns those declarations into one sealed registry per case: every
number, date, imprint, name and surface value an artifact shows, computed once
from the bible, the plan and the seeds, never by a model. Documents and images
then reuse the registry, so the same badge number, issue number or frame count
is the same everywhere, and every visible value is also in the text.

Pure functions, no network, no model calls. See docs/MEDIA.md.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402

ERROR, WARN = "ERROR", "WARN"
TIME_RX = re.compile(r"^([01][0-9]|2[0-3]):([0-5][0-9])$")
NAME_RX = re.compile(r"^[A-Za-z0-9 .,'&-]{2,40}$")
PROSE_ROLES = ("prose", "handwriting", "depiction")
PLATE_KINDS = ("photo", "portrait", "handwriting")


def F(cid: str, path: str = "$", sev: str = ERROR) -> dict:
    return {"id": cid, "path": path, "sev": sev}


# ---------------------------------------------------------------- data access

def forms() -> dict[str, dict]:
    return {f["id"]: f for f in K.data("media_forms")["forms"]}


def calculus() -> dict:
    return K.data("media_calculus")


def media_limits() -> dict:
    return K.data("limits").get("media", {})


def media_clues(plan: dict) -> list[dict]:
    return [c for c in plan["clues"] if c.get("media")]


# ---------------------------------------------------------------- deterministic noise

def _salt(plan: dict, bible: dict, seeds: dict) -> str:
    basis = json.dumps({"seeds": seeds, "inst": bible["premise"]["setting"]["institution"],
                        "clues": sorted(c["id"] for c in plan["clues"])}, sort_keys=True)
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def u(salt: str, *keys) -> float:
    """A stable number in [0, 1) for these keys."""
    h = hashlib.sha256((salt + "|" + "|".join(str(k) for k in keys)).encode("utf-8")).hexdigest()
    return int(h[:12], 16) / float(1 << 48)


def lerp(rng, x: float) -> float:
    lo, hi = rng
    return lo + (hi - lo) * x


# ---------------------------------------------------------------- dates and formats

def parse_date(s) -> dt.date | None:
    if not isinstance(s, str):
        return None
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        return None


def parse_time(s) -> tuple[int, int] | None:
    m = TIME_RX.match(s) if isinstance(s, str) else None
    return (int(m.group(1)), int(m.group(2))) if m else None


def printed_date(d: dt.date) -> str:
    c = calculus()
    return c["printed_date"].format(dd=f"{d.day:02d}", MON=c["months"][d.month - 1], yyyy=d.year)


def long_date(d: dt.date) -> str:
    c = calculus()
    return f"{c['weekdays'][d.weekday()]} {d.day} {c['month_names'][d.month - 1]} {d.year}"


def institution_code(bible: dict, plan: dict) -> str:
    env = plan.get("media_environment") or {}
    if env.get("institution_code"):
        return env["institution_code"]
    rule = calculus()["institution_code"]
    words = re.findall(r"[A-Za-z]+", bible["premise"]["setting"]["institution"])
    code = "".join(w[0].upper() for w in words)[: rule["max_letters"]]
    return code


def _fmt(fmt: str, **kw) -> str:
    return fmt.format(**kw)


def series_regex(fmt: str, inst: str) -> re.Pattern:
    """A regex that finds any value written in this series' format."""
    out, i = "", 0
    for m in re.finditer(r"\{([a-z]+)(?::0?(\d)d)?\}", fmt):
        out += re.escape(fmt[i:m.start()])
        name, width = m.group(1), m.group(2)
        if name == "inst":
            out += re.escape(inst)
        elif name in ("yy",):
            out += r"\d{2}"
        else:
            out += r"\d{" + (width or "1,6") + "}"
        i = m.end()
    out += re.escape(fmt[i:])
    return re.compile(r"(?<![A-Za-z0-9])" + out + r"(?![A-Za-z0-9])")


# ---------------------------------------------------------------- the registry

def _when(clue: dict, salt: str) -> tuple[dt.date, tuple[int, int] | None]:
    d = parse_date(clue.get("date"))
    t = parse_time(clue["media"].get("taken_at"))
    return d, t


def _sequence(salt: str, key: str, items: list[tuple[str, dt.date]]) -> dict[str, int]:
    """Numbers that rise with time: the gap between two items grows with the days between them."""
    spec = calculus()["series"][key]
    out: dict[str, int] = {}
    if not items:
        return out
    items = sorted(items, key=lambda x: (x[1], x[0]))
    seq = int(lerp(spec.get("start", [1, 1]), u(salt, key, "start")))
    rate = lerp(spec.get("per_day", [1, 1]), u(salt, key, "rate"))
    prev = items[0][1]
    for n, (iid, d) in enumerate(items):
        if n:
            gap = (d - prev).days
            seq += max(1, int(round(gap * rate + u(salt, key, iid) * 1.5)))
        out[iid] = seq
        prev = d
    return out


def _people(bible: dict, salt: str, inst: str, archive: dt.date) -> dict[str, dict]:
    c = calculus()
    b = c["badge"]
    issued = {}
    for p in bible["cast"]:
        age = int(lerp(b["age_days"], u(salt, "badge_age", p["id"])))
        issued[p["id"]] = archive - dt.timedelta(days=age)
    spec = c["series"]["badge"]
    seq = int(lerp(spec["start"], u(salt, "badge", "start")))
    out = {}
    for n, pid in enumerate(sorted(issued, key=lambda x: (issued[x], x))):
        if n:
            seq += int(lerp(spec["step"], u(salt, "badge_step", pid)))
        d = issued[pid]
        exp = d + dt.timedelta(days=b["validity_days"])
        out[pid] = {"badge_no": _fmt(spec["format"], inst=inst, seq=seq),
                    "issued": printed_date(d), "issued_iso": d.isoformat(),
                    "expires": printed_date(exp),
                    "clearance": b["clearance"][int(u(salt, "clearance", pid) * len(b["clearance"]))]}
    return out


def archive_date(plan: dict, salt: str) -> dt.date:
    env = plan.get("media_environment") or {}
    if parse_date(env.get("archive_date")):
        return parse_date(env["archive_date"])
    dates = [parse_date(c.get("date")) for c in plan["clues"]]
    dates = [d for d in dates if d]
    last = max(dates) if dates else dt.date(2000, 1, 1)
    lag = int(lerp(calculus()["archive"]["lag_days"], u(salt, "archive")))
    return last + dt.timedelta(days=lag)


def light_regime(climate: str, hemisphere: str, d: dt.date, t: tuple[int, int] | None) -> str:
    regs = calculus()["light_regimes"]
    if climate == "polar":
        r = regs["polar_south" if hemisphere == "south" else "polar_north"]
        if d.month in r["dark_months"]:
            return r["dark"]
        if d.month in r["bright_months"]:
            return r["bright"]
        return r["shoulder"]
    r = regs["default"]
    if t is None:
        return r["shoulder"]
    return r["bright"] if r["day_hours"][0] <= t[0] < r["day_hours"][1] else r["dark"]


def material(form: dict, decl: dict, age_days: int, climate: str, salt: str, iid: str) -> dict:
    """Surface values for the Desk and the image generator. Same inputs, same paper."""
    c = calculus()
    stock = c["stocks"].get(form["stock"])
    if stock is None:
        return {"stock": form["stock"], "age_days": age_days, "legibility": 1.0, "clamped": False}
    cl = c["climates"][climate]
    st = c["storage"][decl.get("storage", "filed")]
    years = max(age_days, 0) / 365.25
    handling = int(decl.get("handling", form["handling_default"]))
    yellow = 1 - math.exp(-years * (0.5 + cl["humidity"]) / stock["yellow_years"])
    fade = 1 - math.exp(-years * (0.3 + cl["light"] * st["light"]) / stock["fade_years"])
    foxing = min(1.0, yellow * cl["humidity"] * 1.5 * stock["foxing"])
    creases = c["folds"][form["fold"]] + handling // 2
    edge = min(1.0, 0.16 * handling * st["wear"] + 0.3 * yellow)
    p_stain = min(0.9, 0.1 * handling + 0.5 * cl["condensation"])
    stains = []
    for k in range(3):
        if u(salt, iid, "stain", k) < p_stain:
            kinds = cl["stains"]
            stains.append({"kind": kinds[int(u(salt, iid, "stain_kind", k) * len(kinds))],
                           "x": round(u(salt, iid, "sx", k), 3), "y": round(u(salt, iid, "sy", k), 3),
                           "r": round(0.04 + 0.12 * u(salt, iid, "sr", k), 3)})
    floor = c["fairness"]["legibility_floor"]

    def legible(f, fx, n):
        return 1 - 0.45 * f - 0.15 * fx - 0.1 * (1 if n else 0)

    clamped = False
    while legible(fade, foxing, len(stains)) < floor:
        clamped = True
        fade, foxing = fade * 0.8, foxing * 0.8
        if stains and legible(fade, foxing, len(stains)) < floor:
            stains = stains[:-1]
    out = {"stock": form["stock"], "age_days": age_days, "yellowing": round(yellow, 3), "ink_fade": round(fade, 3),
           "foxing": round(foxing, 3), "creases": creases, "fold": form["fold"], "edge_wear": round(edge, 3),
           "stains": stains, "legibility": round(legible(fade, foxing, len(stains)), 3), "clamped": clamped}
    if form.get("scanned"):
        out["scan"] = {"skew_deg": round((u(salt, iid, "skew") - 0.5) * 2 * c["scan"]["skew_deg"], 2),
                       "noise": round(lerp(c["scan"]["noise"], u(salt, iid, "noise")), 3), "dpi": c["scan"]["dpi"]}
    return out


def build_registry(plan: dict, bible: dict, seeds: dict) -> dict:
    """Every calculated value for every artifact in the case. Sealed: it lives in checkpoints only."""
    c = calculus()
    fm = forms()
    env = plan.get("media_environment") or {}
    salt = _salt(plan, bible, seeds)
    inst_name = bible["premise"]["setting"]["institution"]
    inst = institution_code(bible, plan)
    archive = archive_date(plan, salt)
    climate = env.get("climate", "temperate")
    hemi = env.get("hemisphere", "north")
    people = _people(bible, salt, inst, archive)
    cast = {p["id"]: p for p in bible["cast"]}
    cameras = {cam["id"]: cam for cam in env.get("cameras", [])}
    pubs = {p["id"]: p for p in env.get("publications", [])}
    mc = media_clues(plan)

    # series numbers, each ordered by date
    by_series: dict[str, list[tuple[str, dt.date]]] = {}
    series_of = {"MF-05": "report", "MF-11": "specimen", "MF-08": "chart", "MF-09": "drawing", "MF-12": "tape"}
    for cl in mc:
        s = series_of.get(cl["media"]["kind"])
        d = parse_date(cl.get("date"))
        if s and d:
            by_series.setdefault(s, []).append((cl["id"], d))
    seqs = {s: _sequence(salt, s, items) for s, items in by_series.items()}
    chart_spec = c["series"]["chart"]
    if by_series.get("chart"):
        first = min(d for _, d in by_series["chart"])
        start = int(lerp(chart_spec["start"], u(salt, "chart", "start")))
        seqs["chart"] = {iid: start + int(round((d - first).days * chart_spec["per_day"][0])) for iid, d in by_series["chart"]}

    # message numbers restart each day
    msgs: dict[str, int] = {}
    day_items: dict[dt.date, list] = {}
    for cl in mc:
        if cl["media"]["kind"] == "MF-07" and parse_date(cl.get("date")):
            day_items.setdefault(parse_date(cl["date"]), []).append(cl)
    for d, items in day_items.items():
        seq = 1 + int(u(salt, "msg", d.isoformat()) * 5)
        for n, cl in enumerate(sorted(items, key=lambda x: (x["media"].get("taken_at") or "", x["id"]))):
            if n:
                seq += 1 + int(u(salt, "msg", cl["id"]) * 3)
            msgs[cl["id"]] = seq

    # frames per camera, in time order, skipping shots that are not in the archive
    frames: dict[str, int] = {}
    for cam_id, cam in cameras.items():
        spec = c["cameras"].get(cam.get("kind"), {})
        shots = [cl for cl in mc if cl["media"].get("camera") == cam_id and parse_date(cl.get("date"))]
        shots.sort(key=lambda x: (x["date"], x["media"].get("taken_at") or "", x["id"]))
        frame = 1 + int(u(salt, "frame0", cam_id) * (spec.get("skip", [0, 0])[1] + 1))
        for n, cl in enumerate(shots):
            if n:
                frame += 1 + int(u(salt, "frame", cl["id"]) * (spec.get("skip", [0, 0])[1] + 1))
            roll = spec.get("roll")
            frames[cl["id"]] = ((frame - 1) % roll) + 1 if roll else frame

    items: dict[str, dict] = {}
    for cl in mc:
        decl = cl["media"]
        form = fm.get(decl["kind"])
        d, t = _when(cl, salt)
        if form is None or d is None:
            continue
        v: dict[str, str] = {}
        kind = decl["kind"]
        cam = cameras.get(decl.get("camera") or "")
        cspec = c["cameras"].get(cam["kind"]) if cam else None
        tm = t or (0, 0)
        stamp = dict(yyyy=d.year, yy=f"{d.year % 100:02d}", mm=f"{d.month:02d}", dd=f"{d.day:02d}", m=d.month, d=d.day,
                     HH=f"{tm[0]:02d}", MM=f"{tm[1]:02d}", SS=f"{int(u(salt, cl['id'], 'ss') * 60):02d}",
                     MON=c["months"][d.month - 1])
        if kind == "MF-01" and cspec:
            if cspec.get("imprint"):
                v["imprint"] = cspec["imprint"].format(cam=cam_id_label(cam), **stamp)
            if cspec.get("frame_label"):
                v["frame"] = cspec["frame_label"].format(frame=frames.get(cl["id"], 1))
        elif kind == "MF-03":
            pid = (decl.get("depicts") or [None])[0]
            if pid in people:
                p = people[pid]
                v.update({"institution": inst_name, "name": f"{cast[pid]['name']['given']} {cast[pid]['name']['family']}",
                          "badge_no": p["badge_no"], "clearance": p["clearance"],
                          "issued": p["issued"], "expires": p["expires"]})
        elif kind == "MF-04":
            pub = pubs.get(decl.get("publication") or "")
            fd = parse_date(pub.get("founded")) if pub else None
            if pub and fd:
                no = (d - fd).days // int(pub.get("cadence_days", 1)) + 1
                vol = d.year - fd.year + 1
                v.update({"masthead": pub["name"], "dateline": long_date(d), "issue_line": f"Vol. {vol} No. {no}"})
        elif kind == "MF-05":
            v.update({"institution": inst_name,
                      "report_no": _fmt(c["series"]["report"]["format"], inst=inst, yy=stamp["yy"], seq=seqs["report"][cl["id"]]),
                      "filed": printed_date(d),
                      "received": printed_date(d + dt.timedelta(days=int(lerp(c["report"]["received_lag_days"], u(salt, cl["id"], "recv")) + 0.5)))})
            if cl["author"] in people:
                v["officer"] = people[cl["author"]]["badge_no"]
        elif kind == "MF-07":
            v.update({"message_no": _fmt(c["series"]["message"]["format"], inst=inst, doy=d.timetuple().tm_yday, seq=msgs.get(cl["id"], 1)),
                      "time_group": f"{stamp['dd']}{stamp['HH']}{stamp['MM']}Z {stamp['MON']} {stamp['yy']}"})
        elif kind == "MF-08":
            v.update({"chart_no": _fmt(c["series"]["chart"]["format"], inst=inst, seq=seqs["chart"][cl["id"]]),
                      "printed_date": printed_date(d)})
        elif kind == "MF-09":
            v["drawing_no"] = _fmt(c["series"]["drawing"]["format"], inst=inst, seq=seqs["drawing"][cl["id"]])
        elif kind == "MF-10":
            v.update({"terminal": _fmt(c["series"]["terminal"]["format"], seq=1 + int(u(salt, "tty", cl["author"]) * 9)),
                      "captured": f"{d.isoformat()} {stamp['HH']}:{stamp['MM']}"})
        elif kind == "MF-11":
            v.update({"specimen_no": _fmt(c["series"]["specimen"]["format"], inst=inst, yy=stamp["yy"], seq=seqs["specimen"][cl["id"]]),
                      "printed_date": printed_date(d)})
        elif kind == "MF-12":
            v.update({"tape_no": _fmt(c["series"]["tape"]["format"], inst=inst, seq=seqs["tape"][cl["id"]]),
                      "timecode": f"{stamp['HH']}:{stamp['MM']}:{stamp['SS']}"})
        anomaly = decl.get("anomaly")
        if anomaly and anomaly.get("value_key") in v:
            v[anomaly["value_key"]] = anomaly["value"]
        age = (archive - d).days
        if kind == "MF-03" and (decl.get("depicts") or [None])[0] in people:
            age = (archive - dt.date.fromisoformat(people[decl["depicts"][0]]["issued_iso"])).days
        items[cl["id"]] = {
            "kind": kind, "values": v, "anomaly": bool(anomaly),
            "camera": decl.get("camera"), "frame": frames.get(cl["id"]),
            "light": light_regime(climate, hemi, d, t) if form["family"] in ("photo", "video") else None,
            "material": material(form, decl, age, climate, salt, cl["id"]),
        }
    patterns = {}
    for key in ("report", "badge", "message", "specimen", "chart", "drawing", "tape"):
        patterns[key] = series_regex(c["series"][key]["format"], inst).pattern
    return {"version": 1, "salt": salt, "institution": {"name": inst_name, "code": inst},
            "archive_date": archive.isoformat(), "climate": climate, "hemisphere": hemi,
            "people": people, "items": items, "patterns": patterns}


def cam_id_label(cam: dict) -> str:
    n = re.findall(r"\d+", cam["id"])
    return f"CAM{int(n[0]):02d}" if n else "CAM01"


def known_values(registry: dict) -> set[str]:
    vals = {p["badge_no"] for p in registry["people"].values()}
    for it in registry["items"].values():
        vals.update(it["values"].values())
    return vals


def required_values(owner: str, registry: dict) -> dict[str, str]:
    """The values this document must carry verbatim: everything its artifact shows."""
    it = registry["items"].get(owner)
    return dict(it["values"]) if it else {}


# ---------------------------------------------------------------- S2 checks

def check_plan_media(plan: dict, bible: dict, seeds: dict) -> list[dict]:
    out: list[dict] = []
    mc = media_clues(plan)
    if not mc:
        return out
    fm = forms()
    c = calculus()
    lim = media_limits()
    env = plan.get("media_environment")
    cast = {p["id"]: p for p in bible["cast"]}
    locs = {l["id"] for l in bible["locations"]}
    phs = {ph["token"]: ph for ph in plan["placeholders"]}

    # environment
    if not isinstance(env, dict) or env.get("climate") not in c["climates"]:
        out.append(F("KT-MD-07", "$.media_environment"))
        env = env if isinstance(env, dict) else {}
    if env.get("hemisphere", "north") not in ("north", "south"):
        out.append(F("KT-MD-07", "$.media_environment.hemisphere"))
    if "archive_date" in env and not parse_date(env["archive_date"]):
        out.append(F("KT-MD-07", "$.media_environment.archive_date"))
    code = institution_code(bible, plan)
    rule = c["institution_code"]
    if not re.fullmatch(r"[A-Z]{%d,%d}" % (rule["min_letters"], rule["max_letters"]), code or ""):
        out.append(F("KT-MD-07", "$.media_environment.institution_code"))
    dates = [parse_date(cl.get("date")) for cl in plan["clues"]]
    years = [d.year for d in dates if d]
    cams = {}
    for i, cam in enumerate(env.get("cameras", [])):
        spec = c["cameras"].get(cam.get("kind"))
        bad = spec is None or cam.get("id") in cams or not str(cam.get("id", "")).startswith("CAM-")
        if spec and years and (min(years) < spec["since"] or (spec["until"] and max(years) > spec["until"])):
            bad = True
        if cam.get("owner") and cam["owner"] not in cast and cam["owner"] not in {d["id"] for d in plan["departments"]}:
            bad = True
        if bad:
            out.append(F("KT-MD-07", f"$.media_environment.cameras[{i}]"))
        cams[cam.get("id")] = cam
    pubs = {}
    for i, pub in enumerate(env.get("publications", [])):
        fd = parse_date(pub.get("founded"))
        cad = pub.get("cadence_days", 1)
        if (not str(pub.get("id", "")).startswith("PUB-") or not NAME_RX.match(str(pub.get("name", "")))
                or fd is None or not isinstance(cad, int) or not 1 <= cad <= 31 or pub.get("id") in pubs):
            out.append(F("KT-MD-07", f"$.media_environment.publications[{i}]"))
        pubs[pub.get("id")] = pub

    # each declaration
    mapped_tokens: dict[str, str] = {}
    for cl in mc:
        i = plan["clues"].index(cl)
        p = f"$.clues[{i}].media"
        decl = cl["media"]
        form = fm.get(decl.get("kind"))
        if form is None:
            out.append(F("KT-MD-01", p + ".kind"))
            continue
        d = parse_date(cl.get("date"))
        if cl["form_id"] not in form["dresses"] or d is None:
            out.append(F("KT-MD-01", p))
        depicts = decl.get("depicts", [])
        for x in depicts:
            ok = (x in cast and "person" in form["depicts"]) or (x in locs and "place" in form["depicts"])
            if not ok:
                out.append(F("KT-MD-01", p + ".depicts"))
                break
        if form.get("depicts_exactly") and (len(depicts) != form["depicts_exactly"] or any(x not in cast for x in depicts)):
            out.append(F("KT-MD-01", p + ".depicts"))
        cam = cams.get(decl.get("camera"))
        if form["camera_kinds"]:
            if cam is None or cam.get("kind") not in form["camera_kinds"]:
                out.append(F("KT-MD-01", p + ".camera"))
        elif decl.get("camera"):
            out.append(F("KT-MD-01", p + ".camera"))
        if form.get("needs_publication"):
            pub = pubs.get(decl.get("publication"))
            if pub is None or (parse_date(pub.get("founded")) and d and parse_date(pub["founded"]) > d):
                out.append(F("KT-MD-01", p + ".publication"))
        needs_time = decl["kind"] in ("MF-07", "MF-10", "MF-12") or (
            decl["kind"] == "MF-01" and cam is not None and cam.get("kind") in ("digital", "cctv"))
        if "taken_at" in decl and parse_time(decl["taken_at"]) is None:
            out.append(F("KT-MD-01", p + ".taken_at"))
        elif needs_time and "taken_at" not in decl:
            out.append(F("KT-MD-01", p + ".taken_at"))
        h = decl.get("handling", form["handling_default"])
        if not isinstance(h, int) or not 0 <= h <= lim.get("max_handling", 5):
            out.append(F("KT-MD-01", p + ".handling"))
        if decl.get("storage", "filed") not in c["storage"]:
            out.append(F("KT-MD-01", p + ".storage"))
        # regions map onto this document's placeholders
        regions = {r["id"]: r for r in form["regions"]}
        rmap = decl.get("regions", {})
        for rid, tok in rmap.items():
            r = regions.get(rid)
            ph = phs.get(tok)
            if (r is None or r["role"] not in PROSE_ROLES or ph is None or ph["owner"] != cl["id"]
                    or ph["stage"] != "S3" or (ph["kind"] == "depiction") != (r["role"] == "depiction")
                    or tok in mapped_tokens):
                out.append(F("KT-MD-01", p + ".regions"))
                break
            mapped_tokens[tok] = cl["id"]
        for r in form["regions"]:
            if r["role"] in PROSE_ROLES and r.get("required") and r["id"] not in rmap:
                out.append(F("KT-MD-01", p + ".regions"))
                break
        # likeness for every person an image shows
        if form.get("plate") in ("photo", "portrait", "video"):
            for x in depicts:
                if x in cast and len(str(cast[x].get("appearance") or "").split()) < 6:
                    out.append(F("KT-MD-03", p + ".depicts"))
                    break
        # declared anomalies: deliberate, fact-bearing, and different from the calculated value
        an = decl.get("anomaly")
        if an is not None:
            keys = {r.get("value") for r in form["regions"] if r["role"] == "registry"}
            if (not isinstance(an, dict) or an.get("value_key") not in keys or an.get("fact") not in cl["facts"]
                    or not re.fullmatch(r"[ -~]{1,40}", str(an.get("value", "")))):
                out.append(F("KT-MD-08", p + ".anomaly"))

    # depiction placeholders belong to a media depiction region
    for i, ph in enumerate(plan["placeholders"]):
        if ph["kind"] == "depiction" and mapped_tokens.get(ph["token"]) != ph["owner"]:
            out.append(F("KT-MD-09", f"$.placeholders[{i}]"))

    # counts
    kinds = [fm[cl["media"]["kind"]] for cl in mc if cl["media"].get("kind") in fm]
    plates = sum(1 for f in kinds if f.get("plate") in PLATE_KINDS)
    videos = sum(1 for f in kinds if f["family"] == "video")
    v = lim.get("video", {})
    if (len(mc) > lim.get("max_items", 99) or plates > lim.get("max_plates", 99) or videos > v.get("max", 1)
            or (v.get("min_enforced") and videos < v.get("min", 0))):
        out.append(F("KT-MD-02", "$.clues"))

    # anomalies must really differ from what the kit would print
    if not any(f["id"] in ("KT-MD-01", "KT-MD-07", "KT-MD-08") for f in out) and any(cl["media"].get("anomaly") for cl in mc):
        clean = json.loads(json.dumps(plan))
        for cl in clean["clues"]:
            if cl.get("media"):
                cl["media"].pop("anomaly", None)
        reg = build_registry(clean, bible, seeds)
        for cl in mc:
            an = cl["media"].get("anomaly")
            if an and reg["items"].get(cl["id"], {}).get("values", {}).get(an["value_key"]) == an["value"]:
                out.append(F("KT-MD-08", f"$.clues[{plan['clues'].index(cl)}].media.anomaly"))
    return out


# ---------------------------------------------------------------- S3 and gate checks

WEEKDAY_DMY = r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})\b"
WEEKDAY_MDY = r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})\b"


def _weekday_errors(text: str) -> bool:
    c = calculus()
    months = {m: i + 1 for i, m in enumerate(c["month_names"])}
    for rx, order in ((WEEKDAY_DMY, "dmy"), (WEEKDAY_MDY, "mdy")):
        for m in re.finditer(rx, text):
            wd = m.group(1)
            if order == "dmy":
                day, mon, yr = int(m.group(2)), m.group(3), int(m.group(4))
            else:
                mon, day, yr = m.group(2), int(m.group(3)), int(m.group(4))
            if mon not in months:
                continue
            try:
                d = dt.date(yr, months[mon], day)
            except ValueError:
                return True
            if c["weekdays"][d.weekday()] != wd:
                return True
    return False


def lint_values(text: str, registry: dict) -> list[str]:
    """IDs of consistency problems in one text: invented series values, wrong weekdays."""
    bad = []
    known = known_values(registry)
    for pat in registry.get("patterns", {}).values():
        for m in re.finditer(pat, text):
            if m.group(0) not in known:
                bad.append("KT-MD-05")
                break
    if _weekday_errors(text):
        bad.append("KT-MD-06")
    return sorted(set(bad))


def lint_fill(fill: dict, owner: str, plan: dict, registry: dict | None) -> list[dict]:
    if not registry:
        return []
    out = []
    texts = [t for t in fill.get("fills", {}).values() if isinstance(t, str)]
    blob = "\n".join(texts)
    for key, val in sorted(required_values(owner, registry).items()):
        if val not in blob:
            out.append(F("KT-MD-04", owner))
            break
    for cid in lint_values(blob, registry):
        out.append(F(cid, owner))
    return out


def lint_consistency(fills_by_owner: dict[str, dict], registry: dict | None) -> list[dict]:
    """KT-MD-05 and KT-MD-06 across every filled document, blaming each owner."""
    if not registry:
        return []
    out = []
    for owner in sorted(fills_by_owner):
        blob = "\n".join(t for t in fills_by_owner[owner].get("fills", {}).values() if isinstance(t, str))
        for cid in lint_values(blob, registry):
            out.append(F(cid, owner))
    return out


# ---------------------------------------------------------------- S3 brief

def brief_for(owner: str, plan: dict, bible: dict, registry: dict | None) -> str:
    clue = next((c for c in plan["clues"] if c["id"] == owner), None)
    if not clue or not clue.get("media") or not registry or owner not in registry["items"]:
        return "This document reaches the player as plain text. Nothing extra to do."
    decl = clue["media"]
    form = forms()[decl["kind"]]
    it = registry["items"][owner]
    phs = {ph["token"]: ph for ph in plan["placeholders"]}
    lines = [f"This document reaches the player as a physical object: {form['name']} ({form['id']})."]
    vals = required_values(owner, registry)
    if vals:
        lines.append("It shows these printed or stamped values. Copy each one exactly, character for character, "
                     "into the text where this kind of paper would print it (a header line, a stamp, a field). "
                     "Never write any other number of these kinds: the kit calculates them.")
        labels = {r.get("value"): r["id"] for r in form["regions"] if r["role"] == "registry"}
        for k in sorted(vals):
            lines.append(f"- {labels.get(k, k).replace('_', ' ')}: {vals[k]}")
    for rid, tok in sorted(decl.get("regions", {}).items()):
        r = next(x for x in form["regions"] if x["id"] == rid)
        if r["role"] == "depiction":
            lines.append(f"- `{tok}` is not printed. Describe plainly what the {form['name']} shows, as an archivist's "
                         "caption would: who is in frame by name, where, doing what, what objects and light. Only what a "
                         "camera could see. No feelings, no meaning, nothing outside this document's facts.")
        elif r["role"] == "handwriting":
            lines.append(f"- `{tok}` is handwritten: keep it to what a person would write by hand, with the author's habits.")
    if it.get("light"):
        lines.append(f"The light at the time: {it['light']}. Keep any mention of light consistent with it.")
    return "\n".join(lines)


def forms_table() -> str:
    rows = []
    for f in K.data("media_forms")["forms"]:
        regions = ", ".join(f"{r['id']} ({r['role']})" for r in f["regions"])
        rows.append(f"- {f['id']} {f['name']}: dresses {', '.join(f['dresses'])}; regions: {regions}"
                    + (f"; cameras: {', '.join(f['camera_kinds'])}" if f["camera_kinds"] else "")
                    + (f"; shows: {', '.join(f['depicts'])}" if f["depicts"] else ""))
    return "\n".join(rows)


def limits_text() -> str:
    lim = media_limits()
    v = lim.get("video", {})
    c = calculus()
    vid = f"at most {v.get('max', 1)} video log"
    if v.get("min_enforced"):
        vid = f"exactly {v.get('min', 1)} video log"
    return (f"At most {lim.get('max_items', 99)} documents carry media; at most {lim.get('max_plates', 99)} of them need a "
            f"generated image (photographs, badges, handwritten scans); {vid}. Climates: {', '.join(c['climates'])}. "
            f"Storage: {', '.join(c['storage'])}. Camera kinds: {', '.join(c['cameras'])}.")


# ---------------------------------------------------------------- finish: manifest and plates

def build_manifest(plan: dict, bible: dict, fills: dict[str, dict], registry: dict, placed: dict[str, str]) -> dict:
    """The player-safe description of every artifact, for the Desk and the image pipeline.

    It holds what the player will see anyway (values, texts, surfaces), and none of
    the plan's private structure: no facts, roles, tiers, routes or anomaly flags.
    """
    fm = forms()
    cast = {p["id"]: p for p in bible["cast"]}
    locs = {l["id"]: l for l in bible["locations"]}
    texts = {tok: txt for f in fills.values() for tok, txt in f.get("fills", {}).items()}
    era = bible["premise"]["setting"]["era"]
    items, plates = [], []
    for cl in media_clues(plan):
        it = registry["items"].get(cl["id"])
        if not it:
            continue
        decl = cl["media"]
        form = fm[decl["kind"]]
        regions = []
        rmap = decl.get("regions", {})
        depiction = None
        for r in form["regions"]:
            if r["role"] == "registry" and r.get("value") in it["values"]:
                regions.append({"id": r["id"], "role": "registry", "text": it["values"][r["value"]]})
            elif r["role"] in ("prose", "handwriting") and r["id"] in rmap:
                tok = rmap[r["id"]]
                regions.append({"id": r["id"], "role": r["role"], "path": placed.get(tok, "$"), "text": texts.get(tok, "")})
            elif r["role"] == "depiction" and r["id"] in rmap:
                depiction = texts.get(rmap[r["id"]], "")
            elif r["role"] == "image":
                regions.append({"id": r["id"], "role": "image"})
        plate_id = None
        if form.get("plate"):
            plate_id = f"IMG-{cl['id']}"
            visible = [x["text"] for x in regions if x["role"] == "registry"]
            if form["plate"] == "handwriting":
                visible = [x["text"] for x in regions if x["role"] in ("handwriting", "prose")]
            plates.append({
                "plate_id": plate_id, "for": cl["id"], "kind": form["plate"], "form": form["id"], "aspect": form["aspect"],
                "style": {"era": era, "camera": (next((cm["kind"] for cm in (plan.get("media_environment") or {}).get("cameras", [])
                                                        if cm["id"] == it.get("camera")), None)),
                          "light": it.get("light"), "climate": registry["climate"]},
                "subjects": [{"id": x, "name": f"{cast[x]['name']['given']} {cast[x]['name']['family']}",
                              "likeness": cast[x].get("appearance", "")} for x in decl.get("depicts", []) if x in cast],
                "places": [{"id": x, "name": locs[x]["name"]} for x in decl.get("depicts", []) if x in locs],
                "depiction": depiction,
                "text_in_image": visible,
                "rules": ["Render only the text listed in text_in_image, exactly; no other legible text.",
                          "Each subject must match their likeness exactly; the same person looks the same in every plate.",
                          "Nothing anachronistic for the era; no logos or brands.",
                          "Show only what the depiction says. Add no people, objects or actions."],
                "material": it["material"],
                "seed": int(registry["salt"][:8], 16) ^ int(hashlib.sha256(cl["id"].encode()).hexdigest()[:8], 16),
            })
        entry = {"id": cl["id"], "form": form["id"], "name": form["name"], "family": form["family"], "aspect": form["aspect"],
                 "regions": regions, "material": it["material"], "plate": plate_id, "alt": depiction}
        if form["family"] == "video":
            words = sum(len(K.words(x.get("text", ""))) for x in regions if x["role"] == "prose")
            secs = int(round(words / calculus()["video"]["words_per_minute"] * 60))
            entry["duration"] = f"{secs // 60:02d}:{secs % 60:02d}"
        items.append(entry)
    return {"version": 1, "institution": registry["institution"], "archive_date": registry["archive_date"],
            "items": items, "plates": plates}


def summary(manifest: dict) -> tuple[int, int, int]:
    items = manifest.get("items", [])
    plates = sum(1 for p in manifest.get("plates", []) if p["kind"] in PLATE_KINDS)
    videos = sum(1 for i in items if i["family"] == "video")
    return len(items), plates, videos
