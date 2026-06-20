# -*- mode: python ; coding: utf-8 -*-
#
# Build with:   pyinstaller DyeMasterPro.spec --clean
#
# Uses --onedir (NOT --onefile) so PyInstaller never extracts files into
# a temporary _MEIxxxxxx folder.  This eliminates the
# "Failed to load Python DLL" / "Failed to import encodings module" errors
# that occur when the updater renames/replaces the exe between runs.
#
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [
    ('version.txt',  '.'),       # bundled inside the folder; updater replaces it
    ('icon.ico',     '.'),
]
binaries       = []
hiddenimports  = [
    'app.gui', 'tkinter', '_tkinter',
    'pandas', 'openpyxl', 'PIL', 'PIL._tkinter_finder',
    'xml.etree.ElementTree', 'pickle', 'logging', 'datetime',
]
hiddenimports += collect_submodules('app')
hiddenimports += collect_submodules('ui')

for pkg in ('openpyxl', 'PIL'):
    tmp = collect_all(pkg)
    datas         += tmp[0]
    binaries      += tmp[1]
    hiddenimports += tmp[2]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_tk_hook.py'],
    excludes=['pytest'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],                     # <-- empty: binaries go into COLLECT (onedir)
    exclude_binaries=True,  # <-- key: keeps DLLs beside the exe
    name='DyeMasterPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,              # UPX can break DLL loading on some systems
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)

# COLLECT puts everything (exe + DLLs + data) into dist/DyeMasterPro/
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='DyeMasterPro',
)
