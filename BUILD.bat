@echo off
REM ========================================
REM DyeMaster Pro - Build Script
REM ========================================

setlocal enabledelayedexpansion

cd /D "%~dp0"

title DyeMaster Pro Builder

echo.
echo ========================================
echo        DyeMaster Pro Builder
echo ========================================
echo.

REM ========================================
REM Check Python
REM ========================================

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    pause
    exit /b 1
)

REM ========================================
REM Check PyInstaller
REM ========================================

python -m pip show pyinstaller >nul 2>&1

if errorlevel 1 (
    echo.
    echo PyInstaller not found.
    echo Installing PyInstaller...
    echo.

    python -m pip install --upgrade pyinstaller

    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install PyInstaller!
        pause
        exit /b 1
    )
)

REM ========================================
REM Clean old build
REM ========================================

echo.
echo Cleaning old build files...

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM ========================================
REM Run PyInstaller
REM ========================================

echo.
echo Building EXE...
echo.

pyinstaller DyeMasterPro.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ========================================
    echo              BUILD FAILED
    echo ========================================
    echo.

    pause
    exit /b 1
)

REM ========================================
REM Verify Output
REM ========================================

if exist "dist\DyeMasterPro\DyeMasterPro.exe" (
    echo.
    echo ========================================
    echo      BUILD COMPLETED SUCCESSFULLY
    echo ========================================
    echo.
    echo EXE:
    echo dist\DyeMasterPro\DyeMasterPro.exe
    echo.
) else (
    echo.
    echo WARNING:
    echo EXE file not found!
    echo Check your .spec file name settings.
    echo.
)

pause
endlocal