# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ["wledflasher/gui.py"],
    pathex=["wled-flasher"],
    binaries=[],
    datas=[("data", "data")],
    hiddenimports=[],
    hookspath=[],
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
    name="WLED Flasher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="data/icons/icon.icns",
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, upx_exclude=[], name="WLED Flasher")
app = BUNDLE(
    coll,
    name="WLED Flasher.app",
    icon="data/icons/icon.icns",
    bundle_identifier=None,
    info_plist={"NSRequiresAquaSystemAppearance": "No"},
)
