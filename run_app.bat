@echo off
REM AWS Architecture Explorer - Run Application
REM Quick launch script for Windows

echo ======================================
echo AWS Architecture Explorer
echo ======================================
echo.

REM Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :check_streamlit
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3
    goto :check_streamlit
)

echo [ERROR] Python is not installed or not in PATH
echo Please install Python: https://www.python.org/downloads/
pause
exit /b 1

:check_streamlit
REM Check if Streamlit is installed
%PYTHON_CMD% -c "import streamlit" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Streamlit is not installed
    echo.
    echo Run deployment script first:
    echo   deploy.bat
    echo.
    pause
    exit /b 1
)

REM Check if app file exists
if not exist "aws_architecture_explorer_app_direct.py" (
    echo [ERROR] Application file not found
    echo   aws_architecture_explorer_app_direct.py
    echo.
    echo Make sure you are in the correct directory
    pause
    exit /b 1
)

REM Run the application
echo Starting Streamlit application...
echo.
echo The app will open in your default browser.
echo Press Ctrl+C to stop the application.
echo.

streamlit run aws_architecture_explorer_app_direct.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to start application
    pause
    exit /b 1
)
