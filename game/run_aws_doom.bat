@echo off
REM AWS DOOM Launcher Script (Windows)

echo ========================================
echo   AWS DOOM - Architecture Explorer
echo ========================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check for pygame
python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo pygame not found. Installing...
    pip install pygame>=2.5.0
)

REM Check for snapshot files
set SNAPSHOT_DIR=%USERPROFILE%\AWS_Architecture_explorer\snapshots
if not exist "%SNAPSHOT_DIR%\*.json" (
    echo.
    echo Warning: No AWS snapshot files found in %SNAPSHOT_DIR%
    echo Please run the snapshot collector first.
    echo.
    pause
    exit /b 1
)

REM Run the game
echo Launching AWS DOOM...
echo.
python aws_doom.py %*
