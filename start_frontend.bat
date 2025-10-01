@echo off
echo ==========================================
echo Starting MODBUS Frontend on Windows
echo ==========================================
echo Backend IP: 192.168.20.192
echo Frontend IP: 192.168.20.100
echo Frontend Port: 3000
echo ==========================================

REM Check if Node.js is available
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Clean and install Node.js dependencies
if exist "frontend\package.json" (
    echo Cleaning up any corrupted dependencies...
    if exist "frontend\node_modules" (
        rmdir /s /q "frontend\node_modules"
    )
    if exist "frontend\package-lock.json" (
        del "frontend\package-lock.json"
    )
    
    echo Installing Node.js dependencies...
    cd frontend
    npm install
    cd ..
)

echo.
echo Starting React Frontend...
echo Frontend will be available at http://192.168.20.100:3000
echo Frontend will connect to backend at http://192.168.20.192:8080/api
echo.

REM Start the frontend
cd frontend
npm start

echo.
echo Frontend stopped.
cd ..
pause
