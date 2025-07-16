@echo off
echo ========================================
echo Interactive MODBUS Attack Launcher
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python or activate your virtual environment
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking required packages...
python -c "import pyModbusTCP" >nul 2>&1
if errorlevel 1 (
    echo Installing pyModbusTCP...
    pip install pyModbusTCP
    if errorlevel 1 (
        echo ERROR: Failed to install pyModbusTCP
        pause
        exit /b 1
    )
)

echo.
echo Starting interactive MODBUS attack...
echo This will:
echo 1. Connect to your Linux VM
echo 2. Read all current register values
echo 3. Allow you to inject custom values
echo 4. Show real-time effects on the frontend
echo.

python interactive_modbus_attack.py

echo.
echo ========================================
echo Interactive attack completed
echo ========================================
pause 