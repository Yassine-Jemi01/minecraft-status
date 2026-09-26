from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

TESTS = [
    "tests.test_advancement_names",
    "tests.test_legacy_support",
    "tests.test_legacy_stats",
    "tests.test_modern_fixtures",
    "tests.test_secure_store",
]


def main() -> int:
    print("=" * 60)
    print("Running Minecraft Status tests")
    print("=" * 60)
    print()
    env = dict(__import__("os").environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(SRC) + ((os.pathsep + existing) if existing else "")
    failed: list[str] = []
    for test in TESTS:
        print("\n" + "=" * 60)
        print(f"Running: {test}")
        print("=" * 60)
        print()
        result = subprocess.run([sys.executable, "-m", test], cwd=ROOT, env=env)
        if result.returncode != 0:
            failed.append(test)
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    if not failed:
        print("All tests passed.")
        return 0
    print("Failed tests:")
    for test in failed:
        print(f"  - {test}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
