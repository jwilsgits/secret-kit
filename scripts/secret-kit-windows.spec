# -*- mode: python ; coding: utf-8 -*-
# Optional PyInstaller spec for Secret Kit Windows portable (onedir).
# Prefer: powershell -File scripts/build-windows.ps1
# From repo root on Windows: pyinstaller scripts/secret-kit-windows.spec
#
# NOTE: build-windows.ps1 uses CLI flags by default; keep this file in sync
# if you switch to the spec path.

from pathlib import Path

try:
    ROOT = Path(SPECPATH).resolve().parent.parent  # noqa: F821 — PyInstaller provides SPECPATH
except NameError:
    ROOT = Path(SPEC).resolve().parent.parent  # noqa: F821

block_cipher = None

datas = [
    (str(ROOT / "ui"), "ui"),
    (str(ROOT / "engine"), "engine"),
    (str(ROOT / "VERSION"), "."),
]

a = Analysis(  # noqa: F821
    [str(ROOT / "app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "webview",
        "webview.platforms.edgechromium",
        "ecdsa",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["objc", "AppKit", "WebKit", "Cocoa", "Quartz", "Foundation"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

try:
    from PyInstaller.utils.hooks import collect_all

    wh_datas, wh_binaries, wh_hidden = collect_all("webview")
    a.datas += wh_datas
    a.binaries += wh_binaries
    a.hiddenimports += list(wh_hidden)
except Exception:
    pass

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SecretKit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SecretKit",
)
