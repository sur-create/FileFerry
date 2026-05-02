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
PYI_WORKDIR = SPEC.parent


def run(command: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd or ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build standalone binaries with PyInstaller")
    parser.add_argument("--clean", action="store_true", help="remove build/dist before building")
    args = parser.parse_args()

    if importlib.util.find_spec("PyInstaller") is None:
        print("error: pyinstaller is not installed. Run: python -m pip install -r requirements-dev.txt")
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

    # Run PyInstaller from the spec directory to avoid repository-root module shadowing
    # (for example local `packaging/` masking site-packages `packaging`).
    dist_path = ROOT / "dist"
    work_path = ROOT / "build"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(dist_path),
        "--workpath",
        str(work_path),
        str(SPEC),
    ]
    try:
        run(command, cwd=PYI_WORKDIR)
    except subprocess.CalledProcessError as exc:
        print(f"error: pyinstaller build failed with exit code {exc.returncode}")
        return exc.returncode
    print("build complete: dist/fileferry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
