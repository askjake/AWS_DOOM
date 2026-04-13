@echo off
REM AWS Architecture Explorer - Windows Deployment Script
REM Batch file wrapper for PowerShell script

echo ======================================
echo AWS Architecture Explorer Deployment
echo ======================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PowerShell is not available
    echo Please install PowerShell or run deploy.ps1 manually
    pause
    exit /b 1
)

REM Run PowerShell script with execution policy bypass
echo Running deployment script...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0deploy.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Deployment failed
    pause
    exit /b 1
)

echo.
echo Deployment completed successfully!
pause
