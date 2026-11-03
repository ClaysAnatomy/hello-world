"""Kit v4.1 data changes, applied key by key so local edits survive.

Run from the project folder (the one holding authoring_kit):
    python apply_data_changes.py            (apply)
    python apply_data_changes.py --check    (report what would change; write nothing)

It edits only these keys and leaves every other value as it is:
  stage_plan.json   S1 outputs; bible_parts; bible_parts_note
  check_catalog.json KT-IO-01..03 (new), KT-BI-01 (reworded)
  limits.json       turns S1 caps, S5 stage cap, repair_unit_caps, caps_note; budget.documents_note
  messages.json     AGENT_TIMEOUT (reworded) and seven new lines
It never touches kit_config.json or capability_map.json. Running it twice is safe.
"""
import json
import sys
from collections import OrderedDict
from pathlib import Path

DATA = Path("authoring_kit") / "data"
CHECK = "--check" in sys.argv

PARTS = [
    {"file": "bible_parts/1_premise.json", "keys": ["kit_version", "mechanism_id", "premise", "critical_strings"],
     "desc": "part 1 of 5: `kit_version`, `mechanism_id`, `premise` and `critical_strings`"},
    {"file": "bible_parts/2_people.json", "keys": ["cast", "locations"], "desc": "part 2 of 5: `cast` and `locations`"},
    {"file": "bible_parts/3_truth.json", "keys": ["truth", "cover"], "desc": "part 3 of 5: `truth` and `cover`"},
    {"file": "bible_parts/4_facts.json", "keys": ["facts"], "desc": "part 4 of 5: `facts`"},
    {"file": "bible_parts/5_reveal.json", "keys": ["aha", "red_herring", "questions"],
     "desc": "part 5 of 5: `aha`, `red_herring` and `questions`"},
]
PARTS_NOTE = ("S1 writes the bible as five small files, one complete write each, and the kit joins them into "
              "checkpoints/bible.json. One long write can hit the model's output limit and fail without a file; "
              "appending in pieces can run out of turns mid-object. Five whole parts keep each write small, make a "
              "cut-off part easy to spot, and let a repair rewrite one part. A part may carry a field listed for "
              "another part; a field set in two parts fails KT-IO-03. When no part exists, a single bible.json is "
              "still accepted.")
IO_CHECKS = OrderedDict([
    ("KT-IO-01", "This output file is missing. Write it."),
    ("KT-IO-02", "This output file is not one complete JSON object. It stops or breaks at the line shown, which "
                 "usually means it was cut off while being written. Write the whole file again in a single write; "
                 "never append to it."),
    ("KT-IO-03", "Two bible parts set the same top-level field. Each field belongs in exactly one part."),
])
BI01 = ("The joined bible must match the bible schema. The path names the field that is wrong, missing, or not "
        "allowed (the bible allows only the fields the schema lists).")
CAPS_NOTE = ("Measured on the first real run (2026-11-02): S1 at 6 turns could not read its three inputs and write a "
             "bible; the repair wrote 261 lines and ran out of turns mid-object. S1 now has 12 turns for 3 reads and "
             "5 part writes with room to fix one. A repair's cap depends on the stage it repairs (repair_unit_caps); "
             "S5 unit_caps is the fallback. With these caps, 6 documents and 2 repairs come to 68 turns, and 12 "
             "documents with 1 repair to 78.")
DOCS_NOTE = ("Research Track 7 sizes the MVP at about 6 clues; 12 is the most the S3 turn cap covers at 3 turns per "
             "document (with one repair inside the 80-turn run cap).")
MESSAGES = [  # (after, key, text)
    (None, "AGENT_TIMEOUT", "AGENT {0} timed out after {1} minutes"),
    ("AGENT_TIMEOUT", "AGENT_TIMEOUT_COST", "AGENT {0} reported no turns or cost: the full turn cap was charged and "
                                            "its cost is unknown (check the provider's usage page)"),
    ("AGENT_TIMEOUT_COST", "AGENT_RESULT", "AGENT {0} result {1}"),
    ("AGENT_RESULT", "AGENT_RAN", "AGENT {0} ran {1} seconds"),
    ("AGENT_RAN", "AGENT_DENIALS", "AGENT {0} permission denials {1}"),
    ("CHECK_FINDING_WARN", "CHECK_FINDING_FILE", "CHECK {0} FAIL {1}"),
    ("CHECK_FINDING_FILE", "CHECK_FINDING_FILE_LINE", "CHECK {0} FAIL {1} at line {2} of {3}"),
    ("BUDGET_STOP_RUN", "BUDGET_COST_UNKNOWN", "BUDGET cost not reported for {0} agent run(s); the cost total is incomplete"),
]

changed = []


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"), object_pairs_hook=OrderedDict)


def save(name, obj, before):
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    if text != before:
        changed.append(name)
        if not CHECK:
            (DATA / name).write_text(text, encoding="utf-8", newline="\n")


def insert_after(d, after, key, value):
    if key in d:
        d[key] = value
        return d
    out = OrderedDict()
    placed = False
    for k, v in d.items():
        out[k] = v
        if k == after:
            out[key] = value
            placed = True
    if not placed:
        out[key] = value
    return out


def stage_plan():
    o = load("stage_plan.json")
    before = json.dumps(o, indent=2, ensure_ascii=False) + "\n"
    next(s for s in o["stages"] if s["id"] == "S1")["outputs"] = [p["file"] for p in PARTS]
    o = insert_after(o, "stages", "bible_parts", PARTS)
    o = insert_after(o, "bible_parts", "bible_parts_note", PARTS_NOTE)
    save("stage_plan.json", o, before)


def check_catalog():
    o = load("check_catalog.json")
    before = json.dumps(o, indent=2, ensure_ascii=False) + "\n"
    checks = OrderedDict()
    for k, v in o["checks"].items():
        if k in IO_CHECKS:
            continue
        if k == "KT-BI-01":
            checks.update(IO_CHECKS)
            v = BI01
        checks[k] = v
    o["checks"] = checks
    save("check_catalog.json", o, before)


def limits():
    o = load("limits.json")
    before = json.dumps(o, indent=2, ensure_ascii=False) + "\n"
    t = o["turns"]
    t["stage_caps"]["S1"] = 12
    t["unit_caps"]["S1"] = 12
    t["stage_caps"]["S5"] = 16
    t = insert_after(t, "unit_caps", "repair_unit_caps",
                     OrderedDict([("S1", 8), ("S2", 8), ("S3", 4), ("S4", 4), ("S6", 3)]))
    t = insert_after(t, "repair_unit_caps", "caps_note", CAPS_NOTE)
    o["turns"] = t
    o["budget"]["documents_note"] = DOCS_NOTE
    save("limits.json", o, before)


def messages():
    o = load("messages.json")
    before = json.dumps(o, indent=2, ensure_ascii=False) + "\n"
    m = o["messages"]
    for after, key, text in MESSAGES:
        m = insert_after(m, after, key, text) if after else (m.__setitem__(key, text) or m)
    o["messages"] = m
    save("messages.json", o, before)


if not DATA.is_dir():
    sys.exit("Run this from the project folder that holds authoring_kit.")
stage_plan()
check_catalog()
limits()
messages()
print(("WOULD CHANGE " if CHECK else "CHANGED ") + (", ".join(changed) if changed else "nothing (already applied)"))
