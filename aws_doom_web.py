#!/usr/bin/env python3
"""
AWS DOOM Web Server
Web-based interface for AWS DOOM game using Flask and Socket.IO
"""

import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Run pygame headless

import pygame
import math
import json
import base64
import io
import socket
from pathlib import Path
from typing import Dict, Any, Optional
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from PIL import Image
import time

# Import game engine components
import sys
sys.path.insert(0, str(Path(__file__).parent))

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'aws-doom-secret-key-2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global game state
game_instance = None
game_running = False
frame_rate = 30  # FPS for web streaming
server_port = None  # Will be set when server starts


def find_available_port(start_port=5000, max_attempts=20):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            # Try to bind to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            continue
    
    # If no port found, return None
    return None


class WebAWSDoomGame:
    """AWS DOOM game adapted for web interface"""
    
    def __init__(self, snapshot_path: str):
        # Import the game classes
        from aws_doom import AWSMap, DoomRenderer, Player
        
        # Initialize pygame in headless mode
        pygame.init()
        pygame.display.set_mode((1, 1))  # Dummy display
        
        # Create offscreen surface for rendering
        self.screen = pygame.Surface((1280, 720))
        self.clock = pygame.time.Clock()
        
        # Load AWS map
        print(f"Loading AWS snapshot for web: {snapshot_path}")
        self.aws_map = AWSMap(snapshot_path)
        print(f"Generated {len(self.aws_map.rooms)} rooms and {len(self.aws_map.walls)} walls")
        
        # Initialize player
        self.player = Player(
            x=self.aws_map.spawn_x,
            y=self.aws_map.spawn_y,
            angle=0,
            keys=[]
        )
        
        # Renderer
        self.renderer = DoomRenderer(self.screen, self.aws_map)
        
        # Game state
        self.show_map = True
        self.running = True
        
        # Input state
        self.keys_pressed = {
            'w': False,
            's': False,
            'a': False,
            'd': False,
            'e': False,
            'm': False
        }
        
    def get_current_room(self):
        """Get the room the player is currently in"""
        for room in self.aws_map.rooms:
            if (room.x <= self.player.x <= room.x + room.width and
                room.y <= self.player.y <= room.y + room.height):
                return room
        return None
    
    def update_input(self, key: str, pressed: bool):
        """Update input state from web client"""
        if key in self.keys_pressed:
            self.keys_pressed[key] = pressed
    
    def handle_movement(self):
        """Process movement based on current input state"""
        from aws_doom import MOVE_SPEED, ROTATE_SPEED
        
        # Movement
        if self.keys_pressed['w']:
            new_x = self.player.x + math.cos(self.player.angle) * MOVE_SPEED
            new_y = self.player.y + math.sin(self.player.angle) * MOVE_SPEED
            if not self.check_collision(new_x, new_y):
                self.player.x = new_x
                self.player.y = new_y
        
        if self.keys_pressed['s']:
            new_x = self.player.x - math.cos(self.player.angle) * MOVE_SPEED
            new_y = self.player.y - math.sin(self.player.angle) * MOVE_SPEED
            if not self.check_collision(new_x, new_y):
                self.player.x = new_x
                self.player.y = new_y
        
        # Rotation
        if self.keys_pressed['a']:
            self.player.angle -= ROTATE_SPEED
        
        if self.keys_pressed['d']:
            self.player.angle += ROTATE_SPEED
        
        # Interaction (only trigger once)
        if self.keys_pressed['e']:
            self.interact()
            self.keys_pressed['e'] = False  # Prevent continuous triggering
        
        # Toggle map (only trigger once)
        if self.keys_pressed['m']:
            self.show_map = not self.show_map
            self.keys_pressed['m'] = False
    
    def check_collision(self, x: float, y: float) -> bool:
        """Check if position collides with walls"""
        collision_radius = 15
        
        for wall in self.aws_map.walls:
            x1, y1 = wall.x1, wall.y1
            x2, y2 = wall.x2, wall.y2
            
            dx = x - x1
            dy = y - y1
            lx = x2 - x1
            ly = y2 - y1
            len_sq = lx * lx + ly * ly
            
            if len_sq == 0:
                continue
            
            t = max(0, min(1, (dx * lx + dy * ly) / len_sq))
            closest_x = x1 + t * lx
            closest_y = y1 + t * ly
            dist = math.sqrt((x - closest_x)**2 + (y - closest_y)**2)
            
            if dist < collision_radius:
                from aws_doom import ResourceType
                if wall.requires_key and wall.resource_id not in self.player.keys:
                    return True
                if wall.resource_type not in [ResourceType.HALLWAY]:
                    return True
        
        return False
    
    def interact(self):
        """Interact with nearby objects"""
        current_room = self.get_current_room()
        if current_room and current_room.requires_key:
            if current_room.resource_id not in self.player.keys:
                self.player.keys.append(current_room.resource_id)
                print(f"✓ Collected key: {current_room.resource_name}")
    
    def render_frame(self) -> str:
        """Render current frame and return as base64 encoded PNG"""
        # Clear screen
        self.screen.fill((0, 0, 0))
        
        # Render 3D view
        self.renderer.render_3d_view(self.player)
        
        # Render minimap if enabled
        if self.show_map:
            self.renderer.render_2d_map(
                self.player,
                self.aws_map.spawn_x - 500,
                self.aws_map.spawn_y - 500
            )
        
        # Render HUD
        current_room = self.get_current_room()
        self.renderer.render_hud(self.player, current_room)
        
        # Convert pygame surface to PIL Image
        frame_string = pygame.image.tostring(self.screen, 'RGB')
        pil_image = Image.frombytes('RGB', (1280, 720), frame_string)
        
        # Convert to base64 PNG
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG', optimize=True, compress_level=1)
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get current game state for HUD updates"""
        current_room = self.get_current_room()
        
        state = {
            'player': {
                'x': int(self.player.x),
                'y': int(self.player.y),
                'angle': self.player.angle,
                'keys_count': len(self.player.keys)
            },
            'current_room': None,
            'show_map': self.show_map
        }
        
        if current_room:
            state['current_room'] = {
                'type': current_room.resource_type.value,
                'name': current_room.resource_name,
                'locked': current_room.requires_key,
                'authorized': current_room.resource_id in self.player.keys,
                'metadata': current_room.metadata
            }
        
        return state


@app.route('/')
def index():
    """Serve the main game page"""
    return render_template('index.html', port=server_port)


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connection_response', {'status': 'connected', 'port': server_port})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


@socketio.on('start_game')
def handle_start_game(data):
    """Initialize and start the game"""
    global game_instance, game_running
    
    snapshot_path = data.get('snapshot_path')
    if not snapshot_path:
        # Find first available snapshot
        snapshot_dir = Path.home() / "AWS_Architecture_explorer" / "snapshots"
        snapshots = list(snapshot_dir.glob("*.json"))
        if snapshots:
            snapshot_path = str(snapshots[0])
        else:
            emit('error', {'message': 'No snapshot files found'})
            return
    
    try:
        game_instance = WebAWSDoomGame(snapshot_path)
        game_running = True
        emit('game_started', {'status': 'success', 'snapshot': Path(snapshot_path).name})
        
        # Start game loop using Socket.IO's background task (eventlet compatible)
        socketio.start_background_task(game_loop)
        
    except Exception as e:
        emit('error', {'message': f'Failed to start game: {str(e)}'})


@socketio.on('key_down')
def handle_key_down(data):
    """Handle key press from client"""
    global game_instance
    if game_instance:
        key = data.get('key', '').lower()
        game_instance.update_input(key, True)


@socketio.on('key_up')
def handle_key_up(data):
    """Handle key release from client"""
    global game_instance
    if game_instance:
        key = data.get('key', '').lower()
        game_instance.update_input(key, False)


@socketio.on('list_snapshots')
def handle_list_snapshots():
    """Return list of available snapshots"""
    snapshot_dir = Path.home() / "AWS_Architecture_explorer" / "snapshots"
    snapshots = []
    
    if snapshot_dir.exists():
        for snap in snapshot_dir.glob("*.json"):
            snapshots.append({
                'name': snap.name,
                'path': str(snap),
                'size': snap.stat().st_size,
                'modified': snap.stat().st_mtime
            })
    
    emit('snapshots_list', {'snapshots': snapshots})


def game_loop():
    """Main game loop running as Socket.IO background task"""
    global game_instance, game_running
    
    print("Game loop started")
    
    while game_running and game_instance:
        try:
            # Handle movement
            game_instance.handle_movement()
            
            # Render frame
            frame_data = game_instance.render_frame()
            
            # Get game state
            state = game_instance.get_game_state()
            
            # Emit frame to all connected clients
            socketio.emit('game_frame', {
                'frame': frame_data,
                'state': state
            })
            
            # Control frame rate using eventlet-compatible sleep
            socketio.sleep(1.0 / frame_rate)
            
        except Exception as e:
            print(f"Game loop error: {e}")
            import traceback
            traceback.print_exc()
            game_running = False
    
    print("Game loop stopped")


def get_local_ip():
    """Get the local IP address"""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"


def main():
    """Start the web server"""
    global server_port
    
    print("=" * 70)
    print("AWS DOOM Web Server")
    print("=" * 70)
    print()
    
    # Find available port
    print("Finding available port...")
    server_port = find_available_port(start_port=5000, max_attempts=20)
    
    if server_port is None:
        print("ERROR: Could not find an available port in range 5000-5019")
        print("Please close other applications using these ports and try again.")
        return
    
    local_ip = get_local_ip()
    
    print(f"Starting Flask server on port {server_port}...")
    print()
    print("Open your browser and navigate to:")
    print(f"  Local:   http://localhost:{server_port}")
    print(f"  Network: http://{local_ip}:{server_port}")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    
    # Run the server
    try:
        socketio.run(app, host='0.0.0.0', port=server_port, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"\nServer error: {e}")


if __name__ == '__main__':
    main()
