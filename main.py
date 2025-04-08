from flask import Flask, request
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

players = {}
pipes = []
game_started = False

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in players:
        del players[request.sid]
        emit('player_disconnected', request.sid, broadcast=True)

@socketio.on('join_game')
def handle_join(data):
    players[request.sid] = {
        'x': 100,
        'y': 300,
        'velocity': 0,
        'score': 0,
        'name': data.get('name', 'Player'),
        'ready': False
    }
    emit('player_joined', {'id': request.sid, 'name': players[request.sid]['name']}, broadcast=True)
    emit('game_state', {'players': players, 'pipes': pipes, 'game_started': game_started})

@socketio.on('player_ready')
def handle_ready():
    if request.sid in players:
        players[request.sid]['ready'] = True
        emit('player_ready', request.sid, broadcast=True)
        
        if all(player['ready'] for player in players.values()) and len(players) > 1:
            start_game()

def start_game():
    global game_started, pipes
    game_started = True
    pipes = []
    for i in range(3):
        add_pipe(400 + i * 300)
    emit('game_started', {'pipes': pipes}, broadcast=True)

def add_pipe(x):
    gap_y = random.randint(150, 450)
    pipes.append({
        'x': x,
        'top_height': gap_y - 150,
        'bottom_y': gap_y + 150
    })

@socketio.on('player_jump')
def handle_jump():
    if request.sid in players:
        players[request.sid]['velocity'] = -10
        emit('player_jumped', request.sid, broadcast=True)

@socketio.on('player_update')
def handle_update(data):
    if request.sid in players and game_started:
        players[request.sid].update(data)

        for pipe in pipes:
            pipe['x'] -= 3
            if pipe['x'] < -50:
                pipes.remove(pipe)
                add_pipe(600)

        emit('game_update', {'players': players, 'pipes': pipes}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
