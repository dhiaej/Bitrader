@echo off
echo ========================================
echo P2P Trading Simulator - Backend Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/6] Python found
echo.

REM Check if MySQL is running
echo [2/6] Checking MySQL...
mysql --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] MySQL client not found in PATH
    echo Make sure MySQL is installed and running
    echo.
)

REM Create virtual environment
echo [3/6] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)
echo.

REM Activate virtual environment and install packages
echo [4/6] Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
echo.

REM Setup environment file
echo [5/6] Setting up environment file...
if not exist ".env" (
    copy .env.example .env
    echo .env file created from .env.example
    echo [IMPORTANT] Please edit .env file with your MySQL credentials!
) else (
    echo .env file already exists
)
echo.

REM Initialize database
echo [6/6] Initializing database...
echo Please make sure:
echo - MySQL is running
echo - Database 'trading_simulator' exists
echo - .env file has correct credentials
echo.
set /p confirm="Do you want to initialize the database now? (y/n): "
if /i "%confirm%"=="y" (
    python -c "from database import init_db; init_db()"
    if errorlevel 1 (
        echo [ERROR] Database initialization failed
        echo Please check your MySQL connection and .env file
    ) else (
        echo Database initialized successfully!
    )
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the backend server:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run server: python main.py
echo.
echo Or run: start_backend.bat
echo.
echo API Documentation will be available at: http://localhost:8000/docs
echo.
pause
