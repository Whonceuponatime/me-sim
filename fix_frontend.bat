@echo off
echo ==========================================
echo Fixing Frontend Dependencies
echo ==========================================

echo Cleaning up corrupted node_modules...
if exist "frontend\node_modules" (
    rmdir /s /q "frontend\node_modules"
    echo Removed corrupted node_modules
)

if exist "frontend\package-lock.json" (
    del "frontend\package-lock.json"
    echo Removed package-lock.json
)

echo.
echo Reinstalling dependencies...
cd frontend
npm install

echo.
echo Starting frontend...
npm start

cd ..
pause
