"""
Build script to create exe file without Python DLL errors.
This script ensures Python DLL is properly bundled.
"""
import os
import sys
import subprocess
import shutil

def clean_build():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist']
    for d in dirs_to_clean:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"Cleaned {d} directory")

def build_exe():
    """Build the exe using PyInstaller with proper DLL handling"""
    
    # Clean previous builds
    clean_build()
    
    # PyInstaller command with options to prevent DLL errors
    cmd = [
        'pyinstaller',
        '--name=ColorChemSystem',
        '--onefile',
        '--windowed',
        '--icon=icon.ico',
        '--add-data=ui;ui',
        '--add-data=app;app',
        '--collect-all=openpyxl',
        '--collect-all=pillow',
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=PIL',
        '--exclude-module=pytest',
        '--exclude-module=tkinter',
        '--runtime-hook=',
        '--debug=all',
        '--pythonflag=',
        'main.py'
    ]
    
    print("Building exe with PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*50)
        print("BUILD SUCCESSFUL!")
        print("="*50)
        print(f"\nExecutable created at: dist/ColorChemSystem.exe")
        
        # Verify the exe exists
        exe_path = os.path.join('dist', 'ColorChemSystem.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"File size: {size_mb:.2f} MB")
        else:
            print("ERROR: Exe file not found!")
            
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Build failed with return code {e.returncode}")
        print("\nTrying alternative method...")
        alternative_build()

def alternative_build():
    """Alternative build method using spec file with fixes"""
    
    # Update spec file with DLL fixes
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        ('python*.dll', '.'),
        ('python3*.dll', '.'),
    ],
    datas=[
        ('ui', 'ui'),
        ('app', 'app'),
    ],
    hiddenimports=[
        'pandas',
        'openpyxl', 
        'PIL',
        'PIL._tkinter_finder',
        'xml.etree.ElementTree',
        'pickle',
        'logging',
        'datetime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'tkinter',
        'distutils',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=True,
    name='ColorChemSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
'''
    
    with open('main.spec', 'w') as f:
        f.write(spec_content)
    
    print("Running PyInstaller with updated spec file...")
    subprocess.run(['pyinstaller', 'main.spec', '--clean'], check=True)
    
    print("\n" + "="*50)
    print("ALTERNATIVE BUILD SUCCESSFUL!")
    print("="*50)

if __name__ == '__main__':
    print("="*50)
    print("ColorChemSystem - EXE Builder")
    print("="*50)
    print(f"Python version: {sys.version}")
    print(f"PyInstaller location: {shutil.which('pyinstaller')}")
    print()
    
    build_exe()
    
    print("\nPress Enter to exit...")
    input()
