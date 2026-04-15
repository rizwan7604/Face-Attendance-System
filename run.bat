@echo off
title Smart Attendance System
cd /d "%~dp0"

echo ==========================================
echo   Smart Attendance System Launcher
echo ==========================================
echo.

REM ---------- Check Python ----------
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not added to PATH.
    echo Please install Python 3.10+ and check "Add Python to PATH".
    echo.
    pause
    exit /b
)

REM ---------- Create virtual environment if missing ----------
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        echo.
        pause
        exit /b
    )
)

REM ---------- Activate virtual environment ----------
call venv\Scripts\activate
if errorlevel 1 (
    echo Failed to activate virtual environment.
    echo.
    pause
    exit /b
)

REM ---------- Upgrade pip ----------
echo Upgrading pip...
python -m pip install --upgrade pip

REM ---------- Install requirements ----------
if exist requirements.txt (
    echo.
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Failed to install requirements.
        echo Please check internet connection and try again.
        echo.
        pause
        exit /b
    )
) else (
    echo requirements.txt not found in project folder.
    echo.
    pause
    exit /b
)

REM ---------- Run app ----------
echo.
echo Starting Smart Attendance System...
python app.py

echo.
if errorlevel 1 (
    echo App closed with an error.
) else (
    echo App closed successfully.
)

echo.
pause