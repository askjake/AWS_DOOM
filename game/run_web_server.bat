@echo off
REM AWS DOOM Web Server Launcher (Windows)

echo ========================================
echo   AWS DOOM - Web Server
echo ========================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check dependencies
echo Checking dependencies...
python -c "import flask" >nul 2>&1 || pip install flask>=3.0.0
python -c "import flask_socketio" >nul 2>&1 || pip install flask-socketio>=5.3.0
python -c "import eventlet" >nul 2>&1 || pip install eventlet>=0.33.0
python -c "import PIL" >nul 2>&1 || pip install pillow>=10.0.0

echo.
echo Starting AWS DOOM Web Server...
echo.
echo Open your browser and navigate to:
echo   http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python aws_doom_web.py
