@echo off
REM AI Fitness Coach - Quick Data Cleanup Script
REM This provides easy access to the data cleanup functionality

echo.
echo ====================================================
echo AI Fitness Coach - Data Log Cleanup Utility
echo ====================================================
echo.

REM Check if Python script exists
if not exist "clear_data_logs.py" (
    echo ERROR: clear_data_logs.py not found in current directory
    echo Please run this script from the AI-FITNESS-COACH directory
    pause
    exit /b 1
)

echo Available options:
echo.
echo 1. Preview cleanup (dry run)
echo 2. Cleanup with backup
echo 3. Quick cleanup (no backup)
echo 4. Full cleanup including calibration data
echo 5. Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo Running preview mode...
    python clear_data_logs.py --dry-run
) else if "%choice%"=="2" (
    echo.
    echo Running cleanup with backup...
    python clear_data_logs.py --backup
) else if "%choice%"=="3" (
    echo.
    echo Running quick cleanup...
    python clear_data_logs.py
) else if "%choice%"=="4" (
    echo.
    echo Running full cleanup...
    python clear_data_logs.py --all --backup
) else if "%choice%"=="5" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice. Please run the script again.
)

echo.
echo Script completed.
pause
