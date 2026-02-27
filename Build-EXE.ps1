# ColorChemSystem EXE Builder - PowerShell Script
# Run this in PowerShell as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ColorChemSystem - EXE Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install required packages
Write-Host "[1/4] Installing required packages..." -ForegroundColor Yellow
pip install pyinstaller==6.11.1 pywin32-ctypes==0.2.3 --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install packages" -ForegroundColor Red
    exit 1
}

# Step 2: Clean previous builds
Write-Host "[2/4] Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# Step 3: Build with PyInstaller
Write-Host "[3/4] Building EXE with PyInstaller..." -ForegroundColor Yellow
pyinstaller --name=ColorChemSystem --onefile --windowed --icon=icon.ico --add-data "ui;ui" --add-data "app;app" --collect-all=openpyxl --collect-all=pillow --hidden-import=pandas --hidden-import=openpyxl --hidden-import=PIL --exclude-module=pytest --exclude-module=tkinter --clean main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    exit 1
}

# Step 4: Verify and report
Write-Host "[4/4] Verifying build..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path "dist\ColorChemSystem.exe") {
    $file = Get-Item "dist\ColorChemSystem.exe"
    $sizeMB = [math]::Round($file.Length / 1MB, 2)
    
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "EXE Location: dist\ColorChemSystem.exe" -ForegroundColor White
    Write-Host "File Size: $sizeMB MB" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "ERROR: EXE file not found!" -ForegroundColor Red
    exit 1
}
