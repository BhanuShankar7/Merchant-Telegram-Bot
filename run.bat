@echo off
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies. Please check your Python and Pip installation.
    pause
    exit /b %errorlevel%
)

echo Starting the bot...
python bot.py
if %errorlevel% neq 0 (
    echo Bot stopped with an error.
    pause
    exit /b %errorlevel%
)
pause
