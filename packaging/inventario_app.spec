# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


# In some environments, PyInstaller executes the spec without defining __file__.
# SPECPATH is provided by PyInstaller and points to the directory containing this spec.
ROOT = Path(SPECPATH).resolve().parent


def _add_data(path: Path, dest: str):
    return (str(path), dest)


datas = []

# App templates
for app in ("core", "inventario", "ventas", "caja", "auditoria"):
    p = ROOT / app / "templates"
    if p.exists():
        datas.append(_add_data(p, f"{app}/templates"))

# Collected static (recommended for Django admin)
if (ROOT / "staticfiles").exists():
    datas.append(_add_data(ROOT / "staticfiles", "staticfiles"))

# Default DB snapshot (copied on first run if runtime db doesn't exist)
if (ROOT / "db.sqlite3").exists():
    datas.append(_add_data(ROOT / "db.sqlite3", "."))

hiddenimports = []
hiddenimports += collect_submodules("django")

# Our project packages are imported dynamically (e.g., DJANGO_SETTINGS_MODULE='core.settings'),
# so we must include them explicitly.
for pkg in ("core", "inventario", "ventas", "caja", "auditoria"):
    hiddenimports += collect_submodules(pkg)

# Keep a few top-level modules explicit as well (helps in edge cases)
hiddenimports += [
    "core",
    "core.settings",
    "core.apps",
    "core.signals",
    "core.urls",
    "core.auth_urls",
    "core.views",
    "core.templatetags",
    "core.templatetags.roles",
    "core.wsgi",
    "core.asgi",
    "auditoria.apps",
    "auditoria.signals",
    "inventario.urls",
    "inventario.templatetags",
    "inventario.templatetags.format_numbers",
    "ventas.urls",
    "caja.urls",
    "auditoria.urls",
]

block_cipher = None


a = Analysis(
    [str(ROOT / "packaging" / "run_inventario_app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Optional Pillow AVIF plugin. Excluding it avoids occasional onefile
        # extraction/decompression issues and reduces bundle size.
        "PIL_avif",
        "PIL._avif",
    ],
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
    name="Inventario",
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
    exclude_binaries=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="Inventario",
)
