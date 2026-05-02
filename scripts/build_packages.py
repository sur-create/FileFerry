#!/usr/bin/env python3
"""Build platform-native installers for FileFerry."""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def resolve_powershell() -> str:
    for candidate in ("pwsh", "powershell"):
        if shutil.which(candidate):
            return candidate
    raise RuntimeError("PowerShell not found")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FileFerry platform packages")
    parser.add_argument("--clean", action="store_true", help="clean and rebuild standalone binary")
    args = parser.parse_args()

    build_cmd = [sys.executable, "scripts/build_binary.py"]
    if args.clean:
        build_cmd.append("--clean")
    try:
        run(build_cmd)
    except subprocess.CalledProcessError as exc:
        print(f"error: binary build failed with exit code {exc.returncode}")
        return exc.returncode

    os_name = platform.system()
    try:
        if os_name == "Windows":
            shell = resolve_powershell()
            run([shell, "-ExecutionPolicy", "Bypass", "-File", "packaging/windows/build_inno.ps1"])
        elif os_name == "Darwin":
            run(["bash", "packaging/macos/build_pkg.sh"])
        elif os_name == "Linux":
            run(["bash", "packaging/linux/build_deb.sh"])
            run(["bash", "packaging/linux/build_rpm.sh"])
        else:
            print(f"error: unsupported platform: {os_name}")
            return 1
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"error: packaging step failed: {exc}")
        return 1

    print("all packaging steps completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
