"""Shared helpers for the authoring kit.

Standard library only, plus jsonschema where schemas are validated.
Everything printed goes through Out.say(), which only accepts fixed
messages from data/messages.json and arguments that are IDs, JSON paths,
trusted engine terms or numbers. Anything else is replaced by WITHHELD,
so model text cannot reach the screen by accident.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator

KIT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = KIT_DIR / "data"
PROMPTS_DIR = KIT_DIR / "prompts"
SCHEMA_DIR = DATA_DIR / "schemas"


class KitError(Exception):
    """A failure with a message ID and printable arguments."""

    def __init__(self, msg_id: str, *args: Any, code: int = 2):
        super().__init__(msg_id)
        self.msg_id = msg_id
        self.args_out = args
        self.code = code


# ---------------------------------------------------------------- files

def load_json(path: Path | str) -> Any:
    # utf-8-sig: Windows tools often start a file with a byte-order mark,
    # which plain utf-8 decoding hands to json as an invalid first character.
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def read_output(path: Path) -> tuple[Any, dict | None]:
    """Read one agent output file. Returns (object, None) or (None, problem).

    problem is {"kind": "missing"} or {"kind": "invalid", "line": n, "lines": total,
    "cut_off": bool}. It never holds any of the file's text.
    """
    try:
        raw = Path(path).read_bytes()
    except OSError:
        return None, {"kind": "missing"}
    text = raw.decode("utf-8-sig", errors="replace")
    total = text.count("\n") + (0 if text.endswith("\n") else 1)
    try:
        return json.loads(text), None
    except ValueError as e:
        line = int(getattr(e, "lineno", 0) or 0)
        stripped = text.rstrip()
        cut = (not stripped) or stripped[-1] not in "}]"
        return None, {"kind": "invalid", "line": line, "lines": total, "cut_off": cut}


def dump_json(obj: Any, path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, path)


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


_DATA_CACHE: dict[str, Any] = {}


def data(name: str, data_dir: Path | None = None) -> Any:
    """Load a kit data file by stem, e.g. data('limits')."""
    base = data_dir or DATA_DIR
    key = str(base / name)
    if key not in _DATA_CACHE:
        _DATA_CACHE[key] = load_json(base / f"{name}.json")
    return _DATA_CACHE[key]


def schema(name: str) -> Any:
    return load_json(SCHEMA_DIR / f"{name}.schema.json")


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


# ---------------------------------------------------------------- validation

def require_jsonschema():
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        raise KitError("ERR_NO_JSONSCHEMA", code=2)
    import jsonschema
    return jsonschema


def schema_errors(instance: Any, schema_obj: Any) -> list[str]:
    """Return JSON paths of schema violations (paths only, never values)."""
    js = require_jsonschema()
    validator_cls = js.validators.validator_for(schema_obj)
    validator = validator_cls(schema_obj)
    paths = []
    for err in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path)):
        base = list(err.absolute_path)
        # Name the field itself for missing or unexpected keys; otherwise every
        # top-level problem reads as a bare "$".
        if err.validator == "required" and isinstance(err.instance, dict):
            missing = [k for k in err.validator_value if k not in err.instance]
            paths.extend(jpath(base + [k]) for k in missing)
            if missing:
                continue
        if (err.validator == "additionalProperties" and err.validator_value is False
                and isinstance(err.instance, dict)):
            allowed = set(err.schema.get("properties", {}))
            pats = [re.compile(px) for px in err.schema.get("patternProperties", {})]
            extra = [k for k in err.instance if k not in allowed and not any(px.search(k) for px in pats)]
            paths.extend(jpath(base + [k]) for k in extra)
            if extra:
                continue
        paths.append(jpath(base))
    return paths or []


# ---------------------------------------------------------------- JSON walking

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def jpath(parts: Iterable[Any]) -> str:
    out = "$"
    for p in parts:
        if isinstance(p, int):
            out += f"[{p}]"
        elif isinstance(p, str) and _IDENT.match(p):
            out += f".{p}"
        else:
            out += "[*]"
    return out


def walk_leaves(obj: Any, parts: tuple = ()) -> Iterator[tuple[tuple, Any]]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_leaves(v, parts + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_leaves(v, parts + (i,))
    else:
        yield parts, obj


def walk_keys(obj: Any) -> Iterator[str]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_keys(v)


def set_at(obj: Any, parts: tuple, value: Any) -> None:
    cur = obj
    for p in parts[:-1]:
        cur = cur[p]
    cur[parts[-1]] = value


def string_leaves(obj: Any) -> list[str]:
    return [v for _, v in walk_leaves(obj) if isinstance(v, str)]


# ---------------------------------------------------------------- placeholders

def placeholder_regex(fmt: str) -> re.Pattern:
    """Build a regex from a format such as 'PP-{owner}-{n}'."""
    pat = re.escape(fmt)
    pat = pat.replace(re.escape("{owner}"), r"(?P<owner>[A-Z0-9][A-Z0-9-]*?)")
    pat = pat.replace(re.escape("{n}"), r"(?P<n>[0-9]{1,3})")
    return re.compile("^" + pat + "$")


def placeholder_search_regex(fmt: str) -> re.Pattern:
    """Same as placeholder_regex but finds tokens inside longer strings."""
    pat = re.escape(fmt)
    pat = pat.replace(re.escape("{owner}"), r"[A-Z0-9][A-Z0-9-]*?")
    pat = pat.replace(re.escape("{n}"), r"[0-9]{1,3}")
    return re.compile(r"(?<![A-Za-z0-9])" + pat + r"(?![0-9])")


def rebuild_case(skeleton: Any, fills: dict[str, str]) -> tuple[Any, dict[str, str]]:
    """Replace whole-string placeholder leaves with fill texts.

    Returns the new case and a map token -> JSON path where it was placed.
    The skeleton is not modified.
    """
    case = json.loads(json.dumps(skeleton))
    placed: dict[str, str] = {}
    for parts, value in list(walk_leaves(case)):
        if isinstance(value, str) and value in fills:
            set_at(case, parts, fills[value])
            placed[value] = jpath(parts)
    return case, placed


def token_paths(obj: Any, rx: re.Pattern) -> dict[str, list[str]]:
    """Map each whole-string token matching rx to the JSON paths holding it."""
    out: dict[str, list[str]] = {}
    for parts, value in walk_leaves(obj):
        if isinstance(value, str) and rx.match(value):
            out.setdefault(value, []).append(jpath(parts))
    return out


# ---------------------------------------------------------------- words

WORD_RX = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z]+)?")


def words(text: str) -> list[str]:
    return [w.lower().replace("’", "'") for w in WORD_RX.findall(text)]


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p for p in parts if words(p)]


def phrase_in(text_lower: str, phrase: str) -> bool:
    phrase = phrase.lower()
    rx = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
    return re.search(rx, text_lower) is not None


def levenshtein(a: str, b: str, cap: int = 3) -> int:
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


# ---------------------------------------------------------------- safe output

class Out:
    """The only way the kit prints. Fixed sentences, IDs, paths, numbers."""

    def __init__(self, stream=None, prefixes: Iterable[str] | None = None,
                 trusted_terms: Iterable[str] = (), path_keys: Iterable[str] | None = None,
                 messages: dict | None = None):
        self.stream = stream or sys.stdout
        lim = data("limits")
        self.prefixes = set(prefixes or lim["ids"]["print_prefixes"])
        self.trusted = set(trusted_terms)
        self.path_keys = set(path_keys) if path_keys is not None else None
        self.messages = messages or data("messages")["messages"]
        self.lines: list[str] = []

    def trust(self, terms: Iterable[str] = (), path_keys: Iterable[str] = ()) -> None:
        self.trusted.update(terms)
        if self.path_keys is None:
            self.path_keys = set()
        self.path_keys.update(path_keys)

    def is_id(self, s: str) -> bool:
        if not re.fullmatch(r"[A-Z0-9]+(-[A-Z0-9]+){0,5}", s) or len(s) > 40:
            return False
        if not re.search(r"[0-9]", s):
            return False
        for i, seg in enumerate(s.split("-")):
            letters = re.match(r"[A-Z]*", seg).group(0)
            if i == 0:
                if letters and letters not in self.prefixes:
                    return False
            elif letters and len(letters) > 2 and letters not in self.prefixes:
                return False
        return True

    def is_path(self, s: str) -> bool:
        if not re.fullmatch(r"\$((\.[A-Za-z_][A-Za-z0-9_]*)|(\[[0-9]{1,5}\])|(\[\*\]))*", s):
            return False
        keys = re.findall(r"\.([A-Za-z_][A-Za-z0-9_]*)", s)
        if not keys:
            return True
        if self.path_keys is None:
            return False
        return all(k in self.path_keys for k in keys)

    def fmt_arg(self, a: Any) -> str:
        if isinstance(a, bool):
            return "YES" if a else "NO"
        if isinstance(a, int):
            return str(a)
        if isinstance(a, float):
            return f"{a:.2f}"
        if isinstance(a, str) and (a in self.trusted or self.is_id(a) or self.is_path(a)):
            return a
        return "WITHHELD"

    def say(self, msg_id: str, *args: Any) -> str:
        template = self.messages.get(msg_id)
        if template is None:
            template = "MESSAGE {0}"
            args = ("WITHHELD",)
        line = template.format(*[self.fmt_arg(a) for a in args])
        self.lines.append(line)
        print(line, file=self.stream, flush=True)
        return line


# ---------------------------------------------------------------- engine terms

def compat_property_names(compat: dict) -> set[str]:
    return set(compat.get("property_names", []))


def kit_schema_keys() -> set[str]:
    keys: set[str] = set()
    for p in SCHEMA_DIR.glob("*.schema.json"):
        keys.update(walk_keys(load_json(p)))
    return keys


def resolve_python(cfg: dict) -> str:
    return cfg.get("python") or sys.executable


def child_env(cfg: dict, agent_key: str = "agent") -> dict:
    env = dict(os.environ)
    default = cfg.get("agent", {}).get("env_strip_suffixes", [])
    suffixes = tuple(cfg.get(agent_key, {}).get("env_strip_suffixes", default))
    for k in list(env):
        if suffixes and k.upper().endswith(suffixes):
            del env[k]
    return env
