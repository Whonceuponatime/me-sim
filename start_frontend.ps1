# PowerShell script to start the ME Simulator frontend
Write-Host "Starting ME Simulator Frontend..." -ForegroundColor Green

# Change to frontend directory
Set-Location -Path ".\frontend"

# Start the development server
Write-Host "Starting React development server..." -ForegroundColor Yellow
npm start 