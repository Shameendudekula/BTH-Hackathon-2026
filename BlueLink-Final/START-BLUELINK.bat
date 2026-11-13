@echo off
setlocal
cd /d "%~dp0"
title BlueLink AI - Local server
if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if not exist ".venv\Scripts\python.exe" goto failed
)
".venv\Scripts\python.exe" -c "import streamlit, requests, bs4" >nul 2>nul
if errorlevel 1 (
    echo Installing required libraries. Internet access is required for first setup.
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" launch.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo BlueLink could not start. Read the error above.
echo Install Python 3.11-3.13 and check your internet connection if dependencies are missing.
pause
exit /b 1
