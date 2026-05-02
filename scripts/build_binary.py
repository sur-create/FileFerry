#!/usr/bin/env python3
"""Build standalone FileFerry binaries with PyInstaller."""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
    "cli": ROOT / "packaging" / "pyinstaller" / "fileferry.spec",
    "gui": ROOT / "packaging" / "pyinstaller" / "fileferry_gui.spec",
}


def run(command: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd or ROOT, check=True)


def _build_spec(spec: Path) -> None:
    spec_workdir = spec.parent
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
        str(spec),
    ]
    run(command, cwd=spec_workdir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build standalone binaries with PyInstaller")
    parser.add_argument("--clean", action="store_true", help="remove build/dist before building")
    parser.add_argument(
        "--target",
        choices=["all", "cli", "gui"],
        default="all",
        help="binary target to build",
    )
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

    targets = ["cli", "gui"] if args.target == "all" else [args.target]
    specs = [SPECS[item] for item in targets]

    for spec in specs:
        if not spec.exists():
            print(f"error: missing spec file: {spec}")
            return 1

        try:
            _build_spec(spec)
        except subprocess.CalledProcessError as exc:
            print(f"error: pyinstaller build failed with exit code {exc.returncode}")
            return exc.returncode

    built = ", ".join(f"dist/{spec.stem.replace('_', '-')}" for spec in specs)
    print(f"build complete: {built}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
