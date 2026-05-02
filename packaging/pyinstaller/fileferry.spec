# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

block_cipher = None
_SPEC_FILE = globals().get("SPEC")
if _SPEC_FILE:
    SPEC_DIR = Path(_SPEC_FILE).resolve().parent
else:
    _cwd = Path.cwd().resolve()
    if (_cwd / "entrypoint.py").exists():
        SPEC_DIR = _cwd
    elif (_cwd / "packaging" / "pyinstaller" / "entrypoint.py").exists():
        SPEC_DIR = _cwd / "packaging" / "pyinstaller"
    else:
        SPEC_DIR = _cwd
for _candidate in (SPEC_DIR, *SPEC_DIR.parents):
    if (_candidate / "pyproject.toml").exists():
        ROOT = _candidate
        break
else:
    ROOT = SPEC_DIR.parents[1]

COMMON_ANALYSIS_KWARGS = dict(
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "README.md"), "."),
        (str(ROOT / "docs" / "user_manual.md"), "docs"),
    ],
    hiddenimports=["fileferry"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

if sys.platform == "win32":
    # GUI entrypoint must be analyzed first so tkinter runtime hooks/data are
    # present in shared onedir runtime files.
    a_gui = Analysis([str(SPEC_DIR / "desktop_entrypoint.py")], **COMMON_ANALYSIS_KWARGS)
    a_cli = Analysis([str(SPEC_DIR / "entrypoint.py")], **COMMON_ANALYSIS_KWARGS)

    pyz_gui = PYZ(a_gui.pure, a_gui.zipped_data, cipher=block_cipher)
    pyz_cli = PYZ(a_cli.pure, a_cli.zipped_data, cipher=block_cipher)

    gui_exe = EXE(
        pyz_gui,
        getattr(a_gui, "dependencies", []),
        a_gui.scripts,
        [],
        exclude_binaries=True,
        name="fileferry",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

    cli_exe = EXE(
        pyz_cli,
        getattr(a_cli, "dependencies", []),
        a_cli.scripts,
        [],
        exclude_binaries=True,
        name="fileferry-cli",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

    coll = COLLECT(
        gui_exe,
        cli_exe,
        a_cli.binaries,
        a_gui.binaries,
        a_cli.zipfiles,
        a_gui.zipfiles,
        a_cli.datas,
        a_gui.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="fileferry",
    )
else:
    a = Analysis([str(SPEC_DIR / "entrypoint.py")], **COMMON_ANALYSIS_KWARGS)
    pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="fileferry",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="fileferry",
    )
