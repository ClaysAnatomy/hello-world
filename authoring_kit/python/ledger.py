"""ledger: the used-seeds ledger.

Each finished run appends salted hashes of the seeds it used, so the next run
can prefer what has not been used recently. The ledger holds no plain IDs or
names: a glance at the file reveals nothing about any case.
"""
from __future__ import annotations

import hashlib
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402


class Ledger:
    def __init__(self, path: Path | None, salt: str | None = None, entries: list | None = None):
        self.path = path
        self.salt = salt or secrets.token_hex(16)
        self.entries = entries or []

    @classmethod
    def load(cls, path: Path | None) -> "Ledger":
        if path and Path(path).is_file():
            obj = K.load_json(path)
            return cls(Path(path), obj.get("salt"), obj.get("entries", []))
        return cls(Path(path) if path else None)

    def h(self, kind: str, value: str) -> str:
        raw = f"{self.salt}|{kind}|{value}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]

    def recent(self, kind: str, value: str, window: int) -> bool:
        target = self.h(kind, value)
        for entry in self.entries[-window:] if window > 0 else []:
            if target in entry.get("hashes", []):
                return True
        return False

    def append(self, run_ref: str, items: list[tuple[str, str]]) -> None:
        self.entries.append({"run": self.h("run", run_ref), "hashes": sorted({self.h(k, v) for k, v in items})})

    def save(self) -> None:
        if self.path is None:
            return
        K.dump_json({"version": 1, "salt": self.salt, "entries": self.entries}, self.path)


def seed_items(seeds: dict) -> list[tuple[str, str]]:
    """The (kind, value) pairs a run records."""
    items: list[tuple[str, str]] = []
    for p in seeds.get("patterns", []):
        items.append(("pattern", p))
    for kind in ("mechanism", "red_herring", "stakes", "human_question", "irony", "setting_texture", "name_pool"):
        if seeds.get(kind):
            items.append((kind, seeds[kind]))
    for person in seeds.get("cast_names", []):
        items.append(("given", person["given"]))
        items.append(("family", person["family"]))
    return items
