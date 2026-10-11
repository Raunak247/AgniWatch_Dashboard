@echo off
title AgniWatch India - One-Click Environment Setup
cd /d "%~dp0"
echo ========================================================
echo   AgniWatch India - Environment Auto-Installer
echo ========================================================
echo.
echo [1/2] Installing Python Dependencies from requirements.txt ...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [2/2] Checking Frontend Node.js dependencies ...
if exist "frontend\package.json" (
    cd frontend
    where npm >nul 2>nul
    if %errorlevel% equ 0 (
        echo Installing npm packages for live development...
        call npm install
    ) else (
        echo Note: npm not detected. Pre-compiled production bundle is ready in frontend\dist!
    )
    cd ..
)

echo.
echo ========================================================
echo   Setup Complete!
echo   You can now launch the platform anytime with: start.bat
echo ========================================================
pause
