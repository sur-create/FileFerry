#!/usr/bin/env python3
"""Build standalone FileFerry binary with PyInstaller."""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "packaging" / "pyinstaller" / "fileferry.spec"


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build standalone binaries with PyInstaller")
    parser.add_argument("--clean", action="store_true", help="remove build/dist before building")
    args = parser.parse_args()

    if importlib.util.find_spec("PyInstaller") is None:
        print("error: pyinstaller is not installed. Run: python3 -m pip install -r requirements-dev.txt")
        return 1

    if args.clean:
        for rel in ("build", "dist"):
            target = ROOT / rel
            if target.exists():
                print(f"remove {target}")
                shutil.rmtree(target)

    if not SPEC.exists():
        print(f"error: missing spec file: {SPEC}")
        return 1

    # Use current interpreter to avoid PATH drift across platforms.
    try:
        run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(SPEC)])
    except subprocess.CalledProcessError as exc:
        print(f"error: pyinstaller build failed with exit code {exc.returncode}")
        return exc.returncode
    print("build complete: dist/fileferry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
