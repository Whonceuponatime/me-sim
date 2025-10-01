@echo off
echo ==========================================
echo Starting MODBUS Frontend on Windows
echo ==========================================
echo Backend IP: 192.168.20.192
echo Frontend IP: 192.168.20.100
echo Bridge Port: 8000
echo Frontend Port: 3000
echo ==========================================

REM Check if Python is available
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating Python virtual environment...
    call venv\Scripts\activate.bat
)

REM Install Python dependencies
if exist "requirements.txt" (
    echo Installing Python dependencies...
    pip install -r requirements.txt
)

REM Install Node.js dependencies
if exist "frontend\package.json" (
    echo Installing Node.js dependencies...
    cd frontend
    npm install
    cd ..
)

echo.
echo Starting MODBUS Bridge Service...
echo Bridge will connect to backend at 192.168.20.192:502
echo Bridge will serve on 192.168.20.100:8000
echo.

REM Start the bridge service in a new window
start "MODBUS Bridge" cmd /k "python modbus_bridge.py --modbus-host 192.168.20.192 --modbus-port 502 --web-host 192.168.20.100 --web-port 8000"

REM Wait a moment for the bridge to start
timeout /t 3 /nobreak >nul

echo Starting React Frontend...
echo Frontend will be available at http://192.168.20.100:3000
echo.

REM Start the frontend
cd frontend
npm start

echo.
echo Frontend stopped.
cd ..
pause
