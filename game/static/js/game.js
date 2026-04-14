// AWS DOOM Web Client

let socket;
let gameStarted = false;
let fps = 0;
let lastFrameTime = Date.now();
let currentPort = window.location.port || '5000';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    setupEventListeners();
    loadSnapshots();
});

function initializeSocket() {
    // Connect to the server (automatically uses current page's port)
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server on port ' + currentPort);
        updateConnectionStatus('Connected (Port ' + currentPort + ')', 'green');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        updateConnectionStatus('Disconnected', 'red');
    });
    
    socket.on('connection_response', function(data) {
        if (data.port) {
            currentPort = data.port;
            updateConnectionStatus('Connected (Port ' + currentPort + ')', 'green');
        }
    });
    
    socket.on('game_started', function(data) {
        console.log('Game started:', data);
        gameStarted = true;
        hideLoadingScreen();
        updateConnectionStatus('Playing: ' + data.snapshot + ' (Port ' + currentPort + ')', 'green');
    });
    
    socket.on('game_frame', function(data) {
        updateGameFrame(data.frame);
        updateGameState(data.state);
        calculateFPS();
    });
    
    socket.on('snapshots_list', function(data) {
        populateSnapshotList(data.snapshots);
    });
    
    socket.on('error', function(data) {
        console.error('Error:', data.message);
        alert('Error: ' + data.message);
    });
}

function setupEventListeners() {
    // Start button
    document.getElementById('start-btn').addEventListener('click', function() {
        const snapshotSelect = document.getElementById('snapshot-list');
        const snapshotPath = snapshotSelect.value;
        startGame(snapshotPath);
    });
    
    // Keyboard controls
    document.addEventListener('keydown', function(e) {
        if (!gameStarted) return;
        
        const key = e.key.toLowerCase();
        if (['w', 'a', 's', 'd', 'e', 'm'].includes(key)) {
            e.preventDefault();
            socket.emit('key_down', { key: key });
        }
    });
    
    document.addEventListener('keyup', function(e) {
        if (!gameStarted) return;
        
        const key = e.key.toLowerCase();
        if (['w', 'a', 's', 'd', 'e', 'm'].includes(key)) {
            e.preventDefault();
            socket.emit('key_up', { key: key });
        }
    });
    
    // Focus game canvas on click
    document.getElementById('game-canvas').addEventListener('click', function() {
        this.focus();
    });
}

function loadSnapshots() {
    socket.emit('list_snapshots');
}

function populateSnapshotList(snapshots) {
    const select = document.getElementById('snapshot-list');
    select.innerHTML = '';
    
    if (snapshots.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No snapshots found';
        select.appendChild(option);
        return;
    }
    
    snapshots.forEach(function(snapshot) {
        const option = document.createElement('option');
        option.value = snapshot.path;
        option.textContent = snapshot.name + ' (' + formatBytes(snapshot.size) + ')';
        select.appendChild(option);
    });
}

function startGame(snapshotPath) {
    console.log('Starting game with snapshot:', snapshotPath);
    socket.emit('start_game', { snapshot_path: snapshotPath });
}

function hideLoadingScreen() {
    document.getElementById('loading-screen').classList.remove('active');
}

function updateConnectionStatus(text, color) {
    const status = document.getElementById('connection-status');
    status.textContent = text;
    status.style.color = color;
}

function updateGameFrame(frameData) {
    const img = document.getElementById('game-frame');
    img.src = frameData;
}

function updateGameState(state) {
    // Update position
    document.getElementById('stat-position').textContent = 
        state.player.x + ', ' + state.player.y;
    
    // Update keys
    document.getElementById('stat-keys').textContent = state.player.keys_count;
    
    // Update current room
    if (state.current_room) {
        document.getElementById('stat-location').textContent = 
            state.current_room.type.toUpperCase();
        
        document.getElementById('resource-type').textContent = 
            state.current_room.name;
        
        // Update access
        if (state.current_room.locked) {
            const access = state.current_room.authorized ? 'AUTHORIZED' : 'LOCKED';
            const color = state.current_room.authorized ? 'green' : 'red';
            document.getElementById('stat-access').innerHTML = 
                '<span style="color: ' + color + '">' + access + '</span>';
        } else {
            document.getElementById('stat-access').innerHTML = 
                '<span style="color: green">OPEN</span>';
        }
        
        // Update metadata
        const metadata = state.current_room.metadata;
        let metadataHtml = '';
        for (const [key, value] of Object.entries(metadata)) {
            metadataHtml += '<div><strong>' + key + ':</strong> ' + value + '</div>';
        }
        document.getElementById('resource-metadata').innerHTML = metadataHtml;
    } else {
        document.getElementById('stat-location').textContent = 'Unknown';
        document.getElementById('resource-type').textContent = 'No resource selected';
        document.getElementById('resource-metadata').innerHTML = '';
        document.getElementById('stat-access').textContent = '-';
    }
}

function calculateFPS() {
    const now = Date.now();
    const delta = now - lastFrameTime;
    fps = Math.round(1000 / delta);
    document.getElementById('stat-fps').textContent = fps;
    lastFrameTime = now;
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
