@echo off
title GST 2B & Tally Book Reconciliation
echo ====================================================================
echo Starting GST 2B and Tally Book Reconciliation Application...
echo Please wait a moment while the server starts.
echo ====================================================================

cd /d "%~dp0"

:: Open the browser after 2 seconds in the background
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

:: Start the Python application
python run.py

pause
