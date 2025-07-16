# MODBUS TCP Attack Script Launcher (PowerShell)
# Run with: powershell -ExecutionPolicy Bypass -File run_attack.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MODBUS TCP Attack Script Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python or activate your virtual environment" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if required packages are installed
Write-Host "Checking required packages..." -ForegroundColor Yellow
try {
    python -c "import pyModbusTCP" 2>$null
    Write-Host "✓ pyModbusTCP package found" -ForegroundColor Green
} catch {
    Write-Host "❌ pyModbusTCP package not found" -ForegroundColor Red
    Write-Host "Installing required packages..." -ForegroundColor Yellow
    
    try {
        pip install pyModbusTCP
        Write-Host "✓ pyModbusTCP installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ ERROR: Failed to install pyModbusTCP" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "Available attack options:" -ForegroundColor Cyan
Write-Host "1. scan    - Scan for MODBUS service" -ForegroundColor White
Write-Host "2. read    - Read current engine state" -ForegroundColor White
Write-Host "3. stop     - Unauthorized engine stop" -ForegroundColor Red
Write-Host "4. start    - Unauthorized engine start" -ForegroundColor Red
Write-Host "5. params   - Parameter manipulation" -ForegroundColor Red
Write-Host "6. monitor  - Continuous monitoring" -ForegroundColor Red
Write-Host "7. full     - Full attack sequence" -ForegroundColor Red
Write-Host ""

$targetIP = Read-Host "Enter Linux VM IP address"
$attackType = Read-Host "Enter attack type (default: full)"

if ([string]::IsNullOrEmpty($attackType)) {
    $attackType = "full"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting attack..." -ForegroundColor Cyan
Write-Host "Target: $targetIP" -ForegroundColor Yellow
Write-Host "Attack: $attackType" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Run the attack script
try {
    python host_attack_script.py $targetIP --attack $attackType
} catch {
    Write-Host "❌ Error running attack script: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Attack completed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit" 