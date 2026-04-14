#!/bin/bash
# AWS DOOM Web Server Launcher

echo "========================================"
echo "  AWS DOOM - Web Server"
echo "========================================"
echo ""

# Check if we're in the right directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3.10+"
    exit 1
fi

# Check for required packages
echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null || { echo "Installing Flask..."; pip install flask>=3.0.0; }
python3 -c "import flask_socketio" 2>/dev/null || { echo "Installing Flask-SocketIO..."; pip install flask-socketio>=5.3.0; }
python3 -c "import eventlet" 2>/dev/null || { echo "Installing eventlet..."; pip install eventlet>=0.33.0; }
python3 -c "import PIL" 2>/dev/null || { echo "Installing Pillow..."; pip install pillow>=10.0.0; }

echo ""
echo "Starting AWS DOOM Web Server..."
echo ""
echo "Open your browser and navigate to:"
echo "  http://localhost:5000"
echo ""
echo "Or from another machine:"
echo "  http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 aws_doom_web.py
