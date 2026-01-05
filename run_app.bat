@echo off
echo ===================================================
echo   Starting Merchant Bot Ecosystem
echo ===================================================

echo 1. Starting Dashboard API...
start "Dashboard API" cmd /k "C:\Users\bhanu\anaconda3\python.exe -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload"

echo 2. Starting Frontend...
cd dashboard
start "Dashboard Frontend" cmd /k "npm run dev"
cd ..

echo 3. Starting Telegram Bot...
start "Telegram Bot" cmd /k "C:\Users\bhanu\anaconda3\python.exe bot.py"

echo ===================================================
echo   All Services Launched!
echo   - API: http://localhost:8000
echo   - Dashboard: http://localhost:5173
echo ===================================================
pause
