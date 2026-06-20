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
REM Create virtual environment if missing
REM ========================================

if not exist "venv\Scripts\activate.bat" (
    echo.
    echo Virtual environment not found. Creating venv...
    echo.

    python -m venv venv

    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
) else (
    echo.
    echo Virtual environment found. Skipping creation.
)

REM ========================================
REM Activate virtual environment
REM ========================================

echo.
echo Activating virtual environment...
call "venv\Scripts\activate.bat"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)

REM ========================================
REM Install requirements.txt
REM ========================================

echo.
echo Installing requirements.txt...
echo.

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install requirements!
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