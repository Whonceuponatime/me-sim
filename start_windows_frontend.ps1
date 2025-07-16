# Windows VM Frontend Startup Script
# This script starts the bridge service and frontend on the Windows VM

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  ME-SIM Windows VM Frontend Startup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "modbus_bridge.py")) {
    Write-Host "Error: modbus_bridge.py not found in current directory" -ForegroundColor Red
    Write-Host "Please run this script from the me-sim project directory" -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Error: Virtual environment not found" -ForegroundColor Red
    Write-Host "Please create virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor White
    Write-Host "  venv\Scripts\activate" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    exit 1
}

# Check if frontend directory exists
if (-not (Test-Path "frontend")) {
    Write-Host "Error: frontend directory not found" -ForegroundColor Red
    Write-Host "Please ensure the frontend directory exists" -ForegroundColor Yellow
    exit 1
}

# Get Linux VM IP from user
$linuxVMIP = Read-Host "Enter Linux VM IP address (default: 192.168.1.100)"
if (-not $linuxVMIP) {
    $linuxVMIP = "192.168.1.100"
}

Write-Host "Network Configuration:" -ForegroundColor Green
Write-Host "  - Linux VM IP: $linuxVMIP" -ForegroundColor White
Write-Host "  - Bridge Port: 8000" -ForegroundColor White
Write-Host "  - Frontend Port: 3000" -ForegroundColor White
Write-Host ""

# Test connectivity to Linux VM
Write-Host "Testing connectivity to Linux VM..." -ForegroundColor Yellow
try {
    $ping = Test-Connection -ComputerName $linuxVMIP -Count 1 -Quiet
    if ($ping) {
        Write-Host "Successfully pinged Linux VM" -ForegroundColor Green
    } else {
        Write-Host "Warning: Could not ping Linux VM" -ForegroundColor Yellow
        Write-Host "   Please check network connectivity" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Warning: Network test failed" -ForegroundColor Yellow
}

# Test MODBUS port
Write-Host "Testing MODBUS port..." -ForegroundColor Yellow
try {
    $tcpTest = Test-NetConnection -ComputerName $linuxVMIP -Port 502 -InformationLevel Quiet
    if ($tcpTest.TcpTestSucceeded) {
        Write-Host "MODBUS port 502 is accessible" -ForegroundColor Green
    } else {
        Write-Host "MODBUS port 502 is not accessible" -ForegroundColor Red
        Write-Host "   Please ensure the Linux VM backend is running" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Could not test MODBUS port" -ForegroundColor Red
}

Write-Host ""

# Function to test Python installation
function Test-PythonInstallation {
    Write-Host "Testing Python installation..." -ForegroundColor Yellow
    
    # Test virtual environment Python
    $pythonExe = "venv\Scripts\python.exe"
    if (Test-Path $pythonExe) {
        try {
            $result = & $pythonExe --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Virtual environment Python found: $pythonExe" -ForegroundColor Green
                return $pythonExe
            }
        } catch {
            Write-Host "Virtual environment Python test failed" -ForegroundColor Red
        }
    }
    
    # Test system Python
    try {
        $result = & python --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "System Python found" -ForegroundColor Green
            return "python"
        }
    } catch {
        Write-Host "System Python test failed" -ForegroundColor Red
    }
    
    Write-Host "Error: No working Python found" -ForegroundColor Red
    return $null
}

# Function to start bridge service
function Start-BridgeService {
    Write-Host "Starting Bridge Service..." -ForegroundColor Green
    Write-Host "   This will connect to Linux VM at $linuxVMIP:502" -ForegroundColor White
    
    # Test Python installation
    $pythonExe = Test-PythonInstallation
    if (-not $pythonExe) {
        return $false
    }
    
    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\activate.ps1"
    
    # Try the simplified bridge script first
    $bridgeScript = "modbus_bridge_simple.py"
    if (-not (Test-Path $bridgeScript)) {
        $bridgeScript = "modbus_bridge.py"
    }
    
    Write-Host "Using bridge script: $bridgeScript" -ForegroundColor White
    Write-Host "Using Python: $pythonExe" -ForegroundColor White
    
    # Start bridge service in background
    Write-Host "Starting bridge service..." -ForegroundColor White
    Start-Process -FilePath $pythonExe -ArgumentList $bridgeScript, "--modbus-host", $linuxVMIP, "--modbus-port", "502" -NoNewWindow
    
    # Wait a moment for service to start
    Start-Sleep -Seconds 5
    
    # Test if bridge service is running
    try {
        Write-Host "Testing bridge service health..." -ForegroundColor Yellow
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET -TimeoutSec 10
        if ($response.status -eq "healthy") {
            Write-Host "Bridge service started successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "Bridge service health check failed" -ForegroundColor Red
            Write-Host "Response: $($response | ConvertTo-Json)" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "Could not connect to bridge service" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "Please check if the service started properly" -ForegroundColor Yellow
        return $false
    }
}

# Function to start frontend
function Start-Frontend {
    Write-Host "Starting Frontend..." -ForegroundColor Green
    Write-Host "   This will start the React development server" -ForegroundColor White
    
    # Navigate to frontend directory
    Set-Location "frontend"
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
        npm install
    }
    
    # Start React development server in background
    Start-Process -FilePath "npm" -ArgumentList "start" -NoNewWindow
    
    # Wait a moment for server to start
    Start-Sleep -Seconds 5
    
    Write-Host "Frontend started successfully" -ForegroundColor Green
    Write-Host "   Open your browser and navigate to: http://localhost:3000" -ForegroundColor Cyan
}

# Start services
$bridgeStarted = Start-BridgeService
if ($bridgeStarted) {
    Start-Frontend
    
    Write-Host ""
    Write-Host "Setup Complete!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Services running:" -ForegroundColor White
    Write-Host "  - Bridge Service: http://localhost:8000" -ForegroundColor White
    Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host "  - MODBUS Backend: $linuxVMIP:502" -ForegroundColor White
    Write-Host ""
    Write-Host "Press any key to stop all services..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    
    # Stop services
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*modbus_bridge*"} | Stop-Process
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process
    
    Write-Host "Services stopped" -ForegroundColor Green
} else {
    Write-Host "Failed to start bridge service" -ForegroundColor Red
    Write-Host "Please check the Linux VM backend is running" -ForegroundColor Yellow
    Write-Host "You can also try running the bridge manually:" -ForegroundColor Yellow
    Write-Host "  venv\Scripts\activate" -ForegroundColor White
    Write-Host "  venv\Scripts\python.exe modbus_bridge_simple.py --modbus-host $linuxVMIP --modbus-port 502" -ForegroundColor White
} 