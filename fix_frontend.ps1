# PowerShell script to fix frontend dependencies
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Fixing Frontend Dependencies" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host "Cleaning up corrupted node_modules..." -ForegroundColor Yellow
if (Test-Path "frontend\node_modules") {
    Remove-Item -Recurse -Force "frontend\node_modules"
    Write-Host "Removed corrupted node_modules" -ForegroundColor Green
}

if (Test-Path "frontend\package-lock.json") {
    Remove-Item -Force "frontend\package-lock.json"
    Write-Host "Removed package-lock.json" -ForegroundColor Green
}

Write-Host ""
Write-Host "Reinstalling dependencies..." -ForegroundColor Yellow
Set-Location frontend
npm install

Write-Host ""
Write-Host "Starting frontend..." -ForegroundColor Green
npm start

Set-Location ..
Read-Host "Press Enter to exit"
