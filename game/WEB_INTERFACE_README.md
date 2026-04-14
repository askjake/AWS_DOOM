# AWS DOOM - Web Interface

## Overview

The AWS DOOM Web Interface allows you to play the game through your browser without needing to install pygame locally. It uses Flask and Socket.IO to stream the game to multiple users simultaneously.

## Features

- 🌐 **Browser-Based**: Play in any modern web browser
- 🎮 **Real-Time Streaming**: Live game frames streamed via WebSocket
- 👥 **Multi-User Ready**: Multiple users can view simultaneously
- 📊 **Live Stats**: Real-time HUD with AWS resource information
- 🎨 **Modern UI**: Clean, responsive web interface
- ⌨️ **Keyboard Controls**: Same controls as desktop version

## Installation

### 1. Install Dependencies

```bash
cd ~/AWS_Architecture_explorer/AWS_DOOM/game
pip install -r requirements_web.txt
```

Or install manually:
```bash
pip install flask flask-socketio pillow python-socketio eventlet pygame
```

### 2. Verify Snapshots

Ensure you have AWS snapshots:
```bash
ls ~/AWS_Architecture_explorer/snapshots/*.json
```

## Usage

### Quick Start

```bash
cd ~/AWS_Architecture_explorer/AWS_DOOM/game
./run_web_server.sh
```

Then open your browser to:
```
http://localhost:5000
```

### Manual Start

```bash
python3 aws_doom_web.py
```

### Access from Other Devices

The server binds to `0.0.0.0` so it's accessible from other machines on your network:

```
http://YOUR_IP:5000
```

Find your IP with:
```bash
hostname -I | awk '{print $1}'
```

## Web Interface Guide

### 1. Loading Screen

- **Select Snapshot**: Choose which AWS snapshot to explore
- **Start Game**: Click to begin

### 2. Game Canvas

- The main area displays the 3D first-person view
- Keyboard controls (W/A/S/D/E/M) work when focused

### 3. Control Panel

- **Controls**: Keyboard reference guide
- **Stats**: Real-time position, keys, location, access status, FPS
- **Resource Info**: Details about current AWS resource
- **Color Guide**: Legend for resource types

### 4. Navigation

- **W**: Move forward
- **S**: Move backward
- **A**: Rotate left
- **D**: Rotate right
- **E**: Interact / Collect key
- **M**: Toggle minimap

## Technical Details

### Architecture

```
┌─────────────┐      WebSocket      ┌──────────────┐
│   Browser   │ ◄────────────────► │ Flask Server │
│  (Client)   │                     │              │
└─────────────┘                     └──────┬───────┘
                                            │
                                    ┌───────▼────────┐
                                    │  Game Engine   │
                                    │   (pygame)     │
                                    └────────────────┘
```

### Components

- **Flask**: Web server framework
- **Socket.IO**: Real-time bidirectional communication
- **pygame**: Headless game engine
- **Pillow**: Image encoding for frame streaming
- **eventlet**: Async server for Socket.IO

### Frame Streaming

1. Game engine renders frame to pygame surface (1280x720)
2. Surface converted to PIL Image
3. Image encoded as PNG and base64 encoded
4. Sent to browser via WebSocket
5. Browser displays as data URI image
6. Target: 30 FPS streaming

### Performance

- **Frame Rate**: 30 FPS (configurable in `aws_doom_web.py`)
- **Latency**: <100ms on local network
- **Bandwidth**: ~500 KB/s per client (PNG compression)
- **Server Load**: Minimal (single game instance shared)

## Configuration

Edit `aws_doom_web.py` to customize:

```python
# Frame rate for web streaming
frame_rate = 30  # Lower for slower connections

# Server binding
socketio.run(app, host='0.0.0.0', port=5000)
```

## Troubleshooting

### "Module 'flask' not found"

Install dependencies:
```bash
pip install -r requirements_web.txt
```

### "Cannot connect to server"

1. Check server is running: `ps aux | grep aws_doom_web`
2. Verify firewall allows port 5000
3. Try `http://127.0.0.1:5000` instead of `localhost`

### Black screen / No frames

1. Check server console for errors
2. Verify pygame is installed: `python3 -c "import pygame"`
3. Ensure snapshot file exists and is valid JSON
4. Check browser console (F12) for errors

### Low FPS / Lag

1. Reduce `frame_rate` in `aws_doom_web.py` (e.g., to 20)
2. Close other applications
3. Use a wired network connection
4. Reduce browser window size

### "No snapshot files found"

Create a snapshot:
```bash
cd ~/AWS_Architecture_explorer
python collect_snapshot.py --region us-west-2 --out snapshots/snapshot.json
```

## Security Notes

⚠️ **Important**: The web server is accessible on your network!

- Server binds to `0.0.0.0` (all interfaces)
- No authentication by default
- Recommended for internal networks only
- For production, add authentication and HTTPS

### Adding Basic Auth (Optional)

Edit `aws_doom_web.py` and add:

```python
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    return username == 'admin' and password == 'your-password'

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')
```

## Comparison: Desktop vs Web

| Feature | Desktop | Web |
|---------|---------|-----|
| Installation | pygame only | Flask + Socket.IO |
| Performance | 60 FPS native | 30 FPS streamed |
| Multi-user | Single player | Multiple viewers |
| Access | Local only | Network accessible |
| Latency | None | <100ms |

## Use Cases

1. **Remote Demos**: Show AWS architecture to remote teams
2. **Training Sessions**: Multiple viewers watch one player
3. **Presentations**: Display on projector via browser
4. **Mobile Access**: Play on tablets/phones
5. **Recording**: Easy to screen-record browser tab

## Development

### Adding Features

Edit these files:

- **Backend**: `aws_doom_web.py` (Flask routes, game loop)
- **Frontend**: `templates/index.html` (HTML structure)
- **Styles**: `static/css/style.css` (Visual design)
- **Client Logic**: `static/js/game.js` (Browser interactions)

### Debug Mode

Enable Flask debug mode:

```python
socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

### Testing

```bash
# Check server responds
curl http://localhost:5000

# Check WebSocket connection
python3 -c "from socketio import Client; c = Client(); c.connect('http://localhost:5000')"
```

## Credits

- **Web Framework**: Flask, Socket.IO
- **Game Engine**: pygame (headless mode)
- **Image Processing**: Pillow
- **Async Server**: eventlet

---

**Enjoy playing AWS DOOM in your browser!** 🌐🎮
