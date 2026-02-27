@echo off
echo ========================================
echo ColorChemSystem - EXE Builder
echo ========================================
echo.

echo Step 1: Installing required packages...
pip install pyinstaller==6.11.1 pywin32-ctypes==0.2.3 --quiet

echo.
echo Step 2: Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

echo.
echo Step 3: Building exe with PyInstaller...
echo.
pyinstaller --name=ColorChemSystem --onefile --windowed --icon=icon.ico --add-data "ui;ui" --add-data "app;app" --collect-all=openpyxl --collect-all=pillow --hidden-import=pandas --hidden-import=openpyxl --hidden-import=PIL --exclude-module=pytest --exclude-module=tkinter main.py

echo.
echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo.
if exist "dist\ColorChemSystem.exe" (
    echo SUCCESS: dist\ColorChemSystem.exe created!
    dir dist\ColorChemSystem.exe
) else (
    echo FAILED: Exe not found. Check errors above.
)
echo.
pause
