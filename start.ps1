Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting AgniWatch India Enterprise Platform" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Free any stray ports first
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess -Force -ErrorAction SilentlyContinue
Stop-Process -Id (Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue).OwningProcess -Force -ErrorAction SilentlyContinue

Write-Host "`n[1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$Root'; python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload"

Write-Host "[2/2] Launching Vite React Dashboard on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$Root\frontend'; npm run dev"

Start-Sleep -Seconds 2
Start-Process "http://localhost:5173"

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "  All services launched successfully!" -ForegroundColor Green
Write-Host "  Dashboard URL : http://localhost:5173" -ForegroundColor White
Write-Host "  API Docs URL  : http://localhost:8000/docs" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Cyan
