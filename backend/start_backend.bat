@echo off
echo ========================================
echo Starting P2P Trading Simulator Backend
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if activation was successful
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    echo Run setup_backend.bat first
    pause
    exit /b 1
)

echo Virtual environment activated
echo.
echo Starting FastAPI server...
echo API Docs: http://localhost:8000/docs
echo Health Check: http://localhost:8000/api/health
echo.

REM Start the server
python main.py

REM If server exits, pause to see error messages
if errorlevel 1 (
    echo.
    echo [ERROR] Server failed to start
    echo Check the error messages above
    pause
)
