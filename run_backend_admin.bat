@echo off
echo Starting MODBUS Backend with Administrator Privileges...
echo This will allow the backend to bind to port 502 (privileged port)

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with Administrator privileges!
) else (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo Starting MODBUS TCP Server on 192.168.20.192:502...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run the backend
echo Executing: python standalone_backend.py --host 192.168.20.192 --port 502
python standalone_backend.py --host 192.168.20.192 --port 502

echo Backend stopped.
pause
