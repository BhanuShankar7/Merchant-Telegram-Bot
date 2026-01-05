@echo off
echo ===================================================
echo   🛑 Stopping All Merchant Bot Services
echo ===================================================

echo Killing Python Processes (Bot & API)...
taskkill /F /IM python.exe /T 2>nul
if %errorlevel% neq 0 echo (No Python processes found or access denied, continuing...)

echo Killing Node Processes (Frontend)...
taskkill /F /IM node.exe /T 2>nul
if %errorlevel% neq 0 echo (No Node processes found or access denied, continuing...)

echo.
echo ⏳ Waiting for cleanup to finish...
timeout /t 3 /nobreak >nul

echo.
echo ===================================================
echo   🚀 Restarting Services
echo ===================================================
call run_app.bat
