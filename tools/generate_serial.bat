@echo off
REM DyeMaster Pro Serial Generator - Double-click to run
REM This script automatically generates a serial for this device and saves it to a TXT file on Desktop.
REM After generation, it will automatically delete the tools folder.

echo DyeMaster Pro Serial Generator
echo ================================
echo.
echo This will automatically generate a serial for your device.
echo Make sure you have Python and venv activated.
echo.

REM Change to project root (assuming this batch is in tools/)
cd /d "%~dp0.."

REM Check if venv exists, if not create it
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Could not create venv. Make sure Python is installed.
        pause
        exit /b 1
    )
    echo Virtual environment created.
)

REM Activate venv (adjust path if needed)
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Could not activate venv. Make sure venv exists.
    pause
    exit /b 1
)

REM Install requirements if not installed (optional, but good)
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo Warning: Could not install requirements. Continuing anyway.
)

REM Set PYTHONPATH to current directory
set PYTHONPATH=%CD%

REM Show device ID first
echo Retrieving device ID...
python -c "from app.licensing import get_device_id; print('Device ID:', get_device_id())"
if errorlevel 1 (
    echo ERROR: Could not retrieve device ID.
    pause
    exit /b 1
)
echo.
pause

REM Generate serial (using fixed license-id DEMO123, output to Desktop)
set DESKTOP=%USERPROFILE%\Desktop
python tools/license_admin.py issue-serial-local --license-id DEMO123 --slot 1 --output "%DESKTOP%\serial.txt" --self-destruct

if errorlevel 1 (
    echo ERROR: Serial generation failed.
    pause
    exit /b 1
)

echo.
echo Serial generated successfully!
echo Check the TXT file on your Desktop: %DESKTOP%\serial.txt
echo The tools folder will be deleted shortly.
echo.
pause

REM Exit
exit /b 0