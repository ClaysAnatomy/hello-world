"""Shared helpers for the kit tests. Standard library only (plus jsonschema via the kit)."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

TESTS = Path(__file__).resolve().parent
KIT = TESTS.parent
sys.path.insert(0, str(KIT / "python"))
sys.path.insert(0, str(TESTS / "fixtures"))

import kitlib as K  # noqa: E402

FIXTURE_ROOT = TESTS / "fixtures" / "engine_root"
FAKE_AGENT = TESTS / "fixtures" / "fake_agent.py"


def override_data(name: str, obj) -> None:
    K._DATA_CACHE[str(K.DATA_DIR / name)] = obj


def reset_data() -> None:
    K._DATA_CACHE.clear()


class Sandbox:
    """A temporary project root holding the fake engine, plus a workspace and an agent folder."""

    def __init__(self, mode_a: bool = True, usage_json: bool = False):
        reset_data()
        self.tmp = Path(tempfile.mkdtemp(prefix="kit_test_"))
        self.root = self.tmp / "project"
        shutil.copytree(FIXTURE_ROOT, self.root)
        self.ws = self.tmp / "sealed" / "CASE-T-01"
        self.agent_dir = self.tmp / "agent_outputs"
        self.agent_dir.mkdir()
        cfg = copy.deepcopy(K.data("kit_config"))
        cfg["mode"] = "A" if mode_a else "B"
        cfg["agent"]["argv"] = [sys.executable, str(FAKE_AGENT), "{max_turns}"]
        cfg["agent"]["usage_from_stdout_json"] = usage_json
        override_data("kit_config", cfg)
        self._env = dict(os.environ)
        os.environ["FAKE_AGENT_DIR"] = str(self.agent_dir)
        os.environ["KITTEST_API_KEY"] = "do-not-pass-me"
        os.environ["KITTEST_AUTH_TOKEN"] = "do-not-pass-me-either"

    def run(self, *argv: str) -> tuple[int, str]:
        import kit_run
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = kit_run.main(list(argv))
        return code, buf.getvalue()

    def kit(self, cmd: str, *extra: str) -> tuple[int, str]:
        return self.run(cmd, "--ws", str(self.ws), *extra)

    def seeds(self) -> dict:
        return json.loads((self.ws / "checkpoints" / "seeds.json").read_text(encoding="utf-8"))

    def calls(self) -> list[dict]:
        p = self.agent_dir / "_calls.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else []

    def close(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        reset_data()
        shutil.rmtree(self.tmp, ignore_errors=True)


def files_under(path: Path):
    for p in sorted(path.rglob("*")):
        if p.is_file():
            yield p


def file_contains(p: Path, needle: str) -> bool:
    try:
        return needle in p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


class Report:
    """Tiny assertion runner so each test file runs as a plain script."""

    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed: list[str] = []

    def check(self, label: str, cond: bool) -> None:
        if cond:
            self.passed += 1
        else:
            self.failed.append(label)
            print(f"FAIL {label}")

    def eq(self, label: str, got, want) -> None:
        ok = got == want
        if not ok:
            print(f"FAIL {label}\n  got:  {got!r}\n  want: {want!r}")
            self.failed.append(label)
        else:
            self.passed += 1

    def finish(self) -> int:
        total = self.passed + len(self.failed)
        print(f"{self.name}: {self.passed} of {total} checks passed")
        return 0 if not self.failed else 1
