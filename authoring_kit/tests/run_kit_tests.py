"""Run every kit test script and print one line per script plus a total.

PowerShell, from the project root:
    python authoring_kit\\tests\\run_kit_tests.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = ["test_kitlib.py", "test_compat_check.py", "test_seed_sampler.py", "test_case_checks.py",
           "test_voice_lint.py", "test_repair_budget_taste.py", "test_brief_builder.py", "test_kit_run.py"]

failed = 0
for name in SCRIPTS:
    proc = subprocess.run([sys.executable, str(HERE / name)], cwd=str(HERE), capture_output=True, text=True)
    last = (proc.stdout.strip().splitlines() or ["no output"])[-1]
    status = "PASS" if proc.returncode == 0 else "FAIL"
    print(f"{status} {last}")
    if proc.returncode != 0:
        failed += 1
        for line in proc.stdout.splitlines():
            if line.startswith("FAIL"):
                print("   " + line)
        if proc.stderr.strip():
            print("   stderr: " + proc.stderr.strip().splitlines()[-1])
print(f"KIT TESTS {len(SCRIPTS) - failed} of {len(SCRIPTS)} scripts passed")
sys.exit(1 if failed else 0)
