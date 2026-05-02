# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
SPEC_DIR = Path(__file__).resolve().parent
ROOT = SPEC_DIR.parents[1]

a = Analysis(
    [str(SPEC_DIR / 'entrypoint.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'README.md'), '.'),
        (str(ROOT / 'docs' / 'user_manual.md'), 'docs'),
    ],
    hiddenimports=['fileferry'],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='fileferry',
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
