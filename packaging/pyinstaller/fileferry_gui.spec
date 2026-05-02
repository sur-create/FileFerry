# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['fileferry_gui/app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('docs/user_manual.md', 'docs'),
    ],
    hiddenimports=['fileferry', 'fileferry_gui'],
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
