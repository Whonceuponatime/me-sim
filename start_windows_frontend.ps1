# PowerShell script to start the Windows frontend
# This script runs the bridge service and frontend on Windows VM (192.168.20.100)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting MODBUS Frontend on Windows" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Backend IP: 192.168.20.192" -ForegroundColor Yellow
Write-Host "Frontend IP: 192.168.20.100" -ForegroundColor Yellow
Write-Host "Bridge Port: 8000" -ForegroundColor Yellow
Write-Host "Frontend Port: 3000" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Node.js is available
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Node.js is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating Python virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

# Install Python dependencies
if (Test-Path "requirements.txt") {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Install Node.js dependencies
if (Test-Path "frontend\package.json") {
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

Write-Host ""
Write-Host "Starting MODBUS Bridge Service..." -ForegroundColor Green
Write-Host "Bridge will connect to backend at 192.168.20.192:502" -ForegroundColor Yellow
Write-Host "Bridge will serve on 192.168.20.100:8000" -ForegroundColor Yellow
Write-Host ""

# Start the bridge service in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python modbus_bridge.py --modbus-host 192.168.20.192 --modbus-port 502 --web-host 192.168.20.100 --web-port 8000"

# Wait a moment for the bridge to start
Start-Sleep -Seconds 3

Write-Host "Starting React Frontend..." -ForegroundColor Green
Write-Host "Frontend will be available at http://192.168.20.100:3000" -ForegroundColor Yellow
Write-Host ""

# Start the frontend
Set-Location frontend
npm start

Write-Host ""
Write-Host "Frontend stopped." -ForegroundColor Red
Set-Location ..
Read-Host "Press Enter to exit"
