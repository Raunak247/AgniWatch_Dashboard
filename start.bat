@echo off
title AgniWatch India Launcher
cd /d "%~dp0"
echo ========================================================
echo   Starting AgniWatch India Enterprise Platform
echo ========================================================
echo.
echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "AgniWatch Backend" cmd /k "cd /d "%~dp0" && python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching Vite React Dashboard on http://localhost:5173 ...
start "AgniWatch Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Waiting 3 seconds for servers to initialize...
timeout /t 3 /nobreak >nul

echo Opening browser at http://localhost:5173 ...
start http://localhost:5173

echo.
echo ========================================================
echo   All services launched successfully!
echo   Frontend Dashboard : http://localhost:5173
echo   Swagger API Docs   : http://127.0.0.1:8000/docs
echo ========================================================
