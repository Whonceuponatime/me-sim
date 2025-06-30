# PowerShell script to start the ME Simulator backend
Write-Host "Starting ME Simulator Backend..." -ForegroundColor Green

# Activate virtual environment if it exists
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
}

# Start the backend server
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
python app.py 