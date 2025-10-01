# PowerShell script to run MODBUS backend with administrator privileges
# This script will request admin privileges and run the backend on port 502

Write-Host "Starting MODBUS Backend with Administrator Privileges..." -ForegroundColor Green
Write-Host "This will allow the backend to bind to port 502 (privileged port)" -ForegroundColor Yellow

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    Start-Process PowerShell -Verb RunAs -ArgumentList "-File `"$PSCommandPath`""
    exit
}

Write-Host "Running with Administrator privileges!" -ForegroundColor Green
Write-Host "Starting MODBUS TCP Server on 192.168.20.192:502..." -ForegroundColor Cyan

# Change to the script directory
Set-Location $PSScriptRoot

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

# Run the backend
Write-Host "Executing: python standalone_backend.py --host 192.168.20.192 --port 502" -ForegroundColor Cyan
python standalone_backend.py --host 192.168.20.192 --port 502

Write-Host "Backend stopped." -ForegroundColor Red
Read-Host "Press Enter to exit"
