@echo off
REM Automatic README Screenshot Updater for Windows
REM This batch file updates the README.md with the most recent screenshot

echo ========================================
echo   README Screenshot Auto-Updater
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Change to scripts directory and run the screenshot updater
echo Updating README with latest screenshot...
echo.
cd /d "%~dp0"
python update_readme_screenshot.py

echo.
echo ========================================
echo   Update Complete!
echo ========================================
echo.
echo To automate this process:
echo 1. Add this batch file to Windows Task Scheduler
echo 2. Or run it manually after taking new screenshots
echo 3. Or use the PowerShell automation script
echo.
pause