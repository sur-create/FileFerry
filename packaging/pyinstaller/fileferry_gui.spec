# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
_SPEC_FILE = globals().get("SPEC")
if _SPEC_FILE:
    SPEC_DIR = Path(_SPEC_FILE).resolve().parent
else:
    _cwd = Path.cwd().resolve()
    if (_cwd / "fileferry_gui" / "app.py").exists():
        SPEC_DIR = _cwd
    elif (_cwd / "packaging" / "pyinstaller" / "fileferry_gui.spec").exists():
        SPEC_DIR = _cwd / "packaging" / "pyinstaller"
    else:
        SPEC_DIR = _cwd
for _candidate in (SPEC_DIR, *SPEC_DIR.parents):
    if (_candidate / "pyproject.toml").exists():
        ROOT = _candidate
        break
else:
    ROOT = SPEC_DIR.parents[1]

a = Analysis(
    [str(ROOT / "fileferry_gui" / "app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "README.md"), "."),
        (str(ROOT / "docs" / "user_manual.md"), "docs"),
    ],
    hiddenimports=["fileferry", "fileferry_gui"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='fileferry-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='fileferry-gui',
)
