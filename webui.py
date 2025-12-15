from game.races_classes import RACES, CLASSES

from flask import Flask, render_template, session, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_mail import Mail, Message
import threading
from game.player import Player
from game.world import World
from game.commands import handle_command
import json
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash


load_dotenv()

app = Flask(__name__, static_folder='web/static', template_folder='web/templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'mud-secret-key')  # For session management

# Flask-Mail configuration (loaded from environment if available)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.example.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your_email@example.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your_email_password')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'your_email@example.com')

mail = Mail(app)
# Explicit async mode for Render (eventlet) and permissive CORS for external clients
socketio = SocketIO(
    app,
    manage_session=False,
    async_mode='eventlet',
    cors_allowed_origins='*'
)

# Test route to verify static file serving (must be after app is defined)
@app.route('/test_cyberpunk_image')
def test_cyberpunk_image():
    return '<img src="/static/cyberpunk_city.jpg" style="max-width:100%">'

ACCOUNTS_FILE = os.path.join('data', 'accounts.json')

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    with open(ACCOUNTS_FILE, 'r') as f:
        return json.load(f)

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts, f)

accounts = load_accounts()

def get_user_info(username):
    info = accounts.get(username)
    if isinstance(info, str):
        # Legacy format: just password hash
        return {'password': info, 'email': '', 'verified': False}
    return info

# In-memory store for web players (keyed by session id)
web_players = {}
world = World()
# Global rule: client-side regen allowed when not in battle (no per-user toggle)
regen_enabled = True

def _is_in_fight(player):
    return bool(getattr(player, 'fight_opponent', None)) and getattr(player, 'fight_hp', None) not in (None, 0)

# Server-side regen: gently recover stats to 100% over ~60 seconds when not in battle
def _start_regen_loop():
    def loop():
        import time
        rate = 100.0 / 60.0  # ~1.67 per second
        while True:
            try:
                if regen_enabled:
                    for username, player in list(web_players.items()):
                        # Skip players in combat
                        if _is_in_fight(player):
                            continue
                        # Regenerate stats toward 100
                        for attr in ('hp', 'endurance', 'willpower'):
                            val = float(getattr(player, attr, 100))
                            if val < 100.0:
                                val = min(100.0, val + rate)
                                setattr(player, attr, round(val))
                        # Emit updated stats to this player's socket room
                        sid = getattr(player, 'address', None)
                        if sid:
                            socketio.emit('player_info', {
                                'name': player.name,
                                'race': player.race,
                                'char_class': player.char_class,
                                'level': player.level,
                                'xp': player.xp,
                                'xp_max': player.xp_max,
                                'credits': getattr(player, 'credits', 0),
                                'inventory': player.inventory,
                                'equipment': getattr(player, 'equipment', {}),
                                'hp': getattr(player, 'hp', 100),
                                'energy': getattr(player, 'energy', 100),
                                'endurance': getattr(player, 'endurance', 100),
                                'willpower': getattr(player, 'willpower', 100),
                                'strength': getattr(player, 'strength', 10),
                                'tech': getattr(player, 'tech', 10),
                                'speed': getattr(player, 'speed', 10),
                                'abilities': getattr(player, 'abilities', []),
                                'effects': [
                                    ('Red Eye', '+10% Attack') if getattr(player, 'attack_boost', 0) > 0 else None,
                                    ('Neon Blade', '+3 Atk, 15% Crit') if getattr(player, 'equipment', {}).get('weapon') == 'Neon Blade' else None
                                ],
                                'current_room': player.current_room,
                                'rooms': world.rooms,
                                'attack': player.get_attack() if hasattr(player, 'get_attack') else getattr(player, 'strength', 10),
                                'attack_boost': getattr(player, 'attack_boost', 0),
                                'fight_opponent': getattr(player, 'fight_opponent', None),
                                'fight_hp': getattr(player, 'fight_hp', None),
                                'room_info': {
                                    'name': player.current_room,
                                    'description': world.rooms[player.current_room]['description'],
                                    'exits': world.rooms[player.current_room]['exits'],
                                    'items': getattr(player, 'room_items', []),
                                    'npcs': world.get_npcs(player.current_room),
                                    'mobs': world.get_mobs_in_room(player.current_room)
                                },
                                'regen_enabled': (regen_enabled and not _is_in_fight(player))
                            }, room=sid)
                time.sleep(1)
            except Exception:
                # Avoid crashing the loop; sleep briefly
                time.sleep(1)
    t = threading.Thread(target=loop, daemon=True)
    t.start()


def _start_mob_loop():
    import time
    def loop():
        while True:
            try:
                world.tick_roaming()
                for username, player in list(web_players.items()):
                    sid = getattr(player, 'address', None)
                    if sid:
                        socketio.emit('player_info', {
                            'name': player.name,
                            'race': player.race,
                            'char_class': player.char_class,
                            'level': player.level,
                            'xp': player.xp,
                            'xp_max': player.xp_max,
                            'inventory': player.inventory,
                            'equipment': getattr(player, 'equipment', {}),
                            'hp': getattr(player, 'hp', 100),
                            'energy': getattr(player, 'energy', 100),
                            'endurance': getattr(player, 'endurance', 100),
                            'willpower': getattr(player, 'willpower', 100),
                            'strength': getattr(player, 'strength', 10),
                            'tech': getattr(player, 'tech', 10),
                            'speed': getattr(player, 'speed', 10),
                            'abilities': getattr(player, 'abilities', []),
                            'effects': [
                                ('Red Eye', '+10% Attack') if getattr(player, 'attack_boost', 0) > 0 else None,
                                ('Neon Blade', '+3 Atk, 15% Crit') if getattr(player, 'equipment', {}).get('weapon') == 'Neon Blade' else None
                            ],
                            'current_room': player.current_room,
                            'rooms': world.rooms,
                            'attack': player.get_attack() if hasattr(player, 'get_attack') else getattr(player, 'strength', 10),
                            'attack_boost': getattr(player, 'attack_boost', 0),
                            'fight_opponent': getattr(player, 'fight_opponent', None),
                            'fight_hp': getattr(player, 'fight_hp', None),
                            'room_info': {
                                'name': player.current_room,
                                'description': world.rooms[player.current_room]['description'],
                                'exits': world.rooms[player.current_room]['exits'],
                                'items': getattr(player, 'room_items', []),
                                'npcs': world.get_npcs(player.current_room),
                                'mobs': world.get_mobs_in_room(player.current_room)
                            },
                            'regen_enabled': (regen_enabled and not _is_in_fight(player))
                        }, room=sid)
                time.sleep(3)
            except Exception:
                time.sleep(3)
    t = threading.Thread(target=loop, daemon=True)
    t.start()


# Ensure background loops start in production servers (e.g., Gunicorn on Render)
_loops_started = False

def _start_background_loops_once():
    global _loops_started
    if not _loops_started:
        _start_regen_loop()
        _start_mob_loop()
        _loops_started = True

# Start background loops upon module import (Flask 3 removed before_first_request)
_start_background_loops_once()

@app.route('/')
def index():
    # Always redirect to login if not authenticated
    if not session.get('username'):
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in accounts and check_password_hash(accounts[username]['password'], password):
            session['username'] = username
            # Require race/class selection if not set
            user = accounts[username]
            if not user.get('race') or not user.get('char_class'):
                return redirect(url_for('choose_race_class'))
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password.'
    return render_template('login.html', error=error)




@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if not username or not password or not email:
            error = 'Username, password, and email required.'
        elif username in accounts:
            error = 'Username already exists.'
        else:
            accounts[username] = {
                'password': generate_password_hash(password),
                'email': email,
                'verified': False,
                'race': None,
                'char_class': None,
                'credits': 100
            }
            save_accounts(accounts)
            # Send verification email
            try:
                token = username  # Simple token for demo
                verify_url = url_for('verify_email', username=token, _external=True)
                msg = Message('Verify your MUD account', recipients=[email])
                msg.body = f'Click to verify your account: {verify_url}'
                mail.send(msg)
                success = 'Account created! Check your email to verify.'
            except Exception as e:
                error = f'Error sending email: {e}'
    return render_template('register.html', error=error, success=success)

# Race/Class selection page
@app.route('/choose_race_class', methods=['GET', 'POST'])
def choose_race_class():
    if not session.get('username'):
        return redirect(url_for('login'))
    username = session['username']
    if request.method == 'POST':
        char_name = request.form.get('char_name', '').strip()
        race = request.form.get('race')
        char_class = request.form.get('char_class')
        if not char_name or not race or not char_class or race not in RACES or char_class not in CLASSES:
            return render_template('choose_race_class.html', error='Please enter a name and select a valid race and class.', races=RACES, classes=CLASSES)
        accounts[username]['char_name'] = char_name
        accounts[username]['race'] = race
        accounts[username]['char_class'] = char_class
        save_accounts(accounts)
        return redirect(url_for('index'))
    return render_template('choose_race_class.html', races=RACES, classes=CLASSES)
# Admin tools
ADMIN_USER = 'admin'
ADMIN_PASS = generate_password_hash('adminpass')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error = None
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username')
        if action == 'delete' and username in accounts:
            del accounts[username]
            save_accounts(accounts)
    return render_template('admin.html', users=accounts)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and check_password_hash(ADMIN_PASS, password):
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Invalid admin credentials.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    # Persist equipment and progression on logout if possible
    username = session.get('username')
    if username and username in web_players and username in accounts:
        player = web_players.get(username)
        try:
            accounts[username]['equipment'] = dict(getattr(player, 'equipment', {}))
            accounts[username]['xp'] = getattr(player, 'xp', accounts[username].get('xp', 0))
            accounts[username]['level'] = getattr(player, 'level', accounts[username].get('level', 1))
            accounts[username]['xp_max'] = getattr(player, 'xp_max', accounts[username].get('xp_max', 100))
            accounts[username]['credits'] = int(getattr(player, 'credits', accounts[username].get('credits', 0)))
            accounts[username]['inventory'] = list(getattr(player, 'inventory', accounts[username].get('inventory', [])))
            accounts[username]['current_room'] = getattr(player, 'current_room', accounts[username].get('current_room', world.start_room))
            for attr in ('hp', 'energy', 'endurance', 'willpower'):
                accounts[username][attr] = int(getattr(player, attr, accounts[username].get(attr, 100)))
            save_accounts(accounts)
        except Exception:
            pass
    session.pop('username', None)
    return redirect(url_for('login'))


@socketio.on('connect')
def handle_connect():
    sid = request.sid
    username = session.get('username')
    if not username:
        emit('message', {'data': 'Not authenticated. Please log in.'})
        return
    # Create a new Player for this session
    acc = accounts.get(username, {})
    player = Player(address=sid, start_room=world.start_room)
    player.username = username
    # Use character name if set, else fallback to username
    player.name = acc.get('char_name', username)
    # Set race and class from account info
    player.race = acc.get('race')
    player.char_class = acc.get('char_class')
    # Restore persisted equipment if available
    if isinstance(acc.get('equipment'), dict):
        try:
            player.equipment.update(acc.get('equipment'))
        except Exception:
            pass
    # Restore persisted progression if available
    if 'level' in acc:
        try:
            player.level = int(acc.get('level', player.level))
        except Exception:
            pass
    if 'xp' in acc:
        try:
            player.xp = int(acc.get('xp', player.xp))
        except Exception:
            pass
    # Restore credits if available
    try:
        player.credits = int(acc.get('credits', getattr(player, 'credits', 100)))
    except Exception:
        pass
    if 'xp_max' in acc:
        try:
            player.xp_max = int(acc.get('xp_max', player.xp_max))
        except Exception:
            pass
    # Restore inventory if available
    if isinstance(acc.get('inventory'), list):
        try:
            player.inventory = list(acc.get('inventory'))
        except Exception:
            pass
    # Restore last location if available
    if isinstance(acc.get('current_room'), str) and acc.get('current_room') in world.rooms:
        try:
            player.current_room = acc.get('current_room')
        except Exception:
            pass
    # Restore core stats if available
    for attr in ('hp', 'energy', 'endurance', 'willpower'):
        if attr in acc:
            try:
                setattr(player, attr, int(acc.get(attr)))
            except Exception:
                pass
    web_players[username] = player
    welcome = world.describe_room(player.current_room)
    emit('message', {'data': f'Welcome {username}!\n{welcome}'})
    emit('player_info', {
        'name': player.name,
        'race': player.race,
        'char_class': player.char_class,
        'level': player.level,
        'xp': player.xp,
        'xp_max': player.xp_max,
        'credits': getattr(player, 'credits', 0),
        'inventory': player.inventory,
        'equipment': getattr(player, 'equipment', {}),
        'hp': getattr(player, 'hp', 100),
        'energy': getattr(player, 'energy', 100),
        'endurance': getattr(player, 'endurance', 100),
        'willpower': getattr(player, 'willpower', 100),
        'strength': getattr(player, 'strength', 10),
        'tech': getattr(player, 'tech', 10),
        'speed': getattr(player, 'speed', 10),
        'abilities': getattr(player, 'abilities', []),
        'effects': [
            ('Red Eye', '+10% Attack') if getattr(player, 'attack_boost', 0) > 0 else None,
            ('Neon Blade', '+3 Atk, 15% Crit') if getattr(player, 'equipment', {}).get('weapon') == 'Neon Blade' else None
        ],
        'current_room': player.current_room,
        'rooms': world.rooms,
        'attack': player.get_attack() if hasattr(player, 'get_attack') else getattr(player, 'strength', 10),
        'attack_boost': getattr(player, 'attack_boost', 0),
        'fight_opponent': getattr(player, 'fight_opponent', None),
        'fight_hp': getattr(player, 'fight_hp', None),
        'room_info': {
            'name': player.current_room,
            'description': world.rooms[player.current_room]['description'],
            'exits': world.rooms[player.current_room]['exits'],
            'items': getattr(player, 'room_items', []),
            'npcs': world.get_npcs(player.current_room),
            'mobs': world.get_mobs_in_room(player.current_room)
        },
        'regen_enabled': (regen_enabled and not _is_in_fight(player))
    })

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    player = web_players.get(username)
    # Notify players in the same room that this user disconnected
    if player is not None:
        room = getattr(player, 'current_room', None)
        for u, p in list(web_players.items()):
            if u != username and getattr(p, 'current_room', None) == room:
                sid_room = getattr(p, 'address', None)
                if sid_room:
                    socketio.emit('message', {'data': f"{player.name} disconnects."}, room=sid_room)
    if username in web_players:
        del web_players[username]

@socketio.on('command')
def handle_command_event(data):
    username = session.get('username')
    player = web_players.get(username)
    if not player:
        emit('message', {'data': 'Session error. Please reconnect.'})
        return
    command = data.get('command', '').strip()
    if command.lower() in ('quit', 'exit'):
        emit('message', {'data': 'Goodbye!'})
        return
    # Built-in command: who (online players)
    if command.lower() == 'who':
        online = list(web_players.keys())
        emit('message', {'data': f"Players online ({len(online)}): " + ", ".join(online)})
        return
    # Intercept name change to persist it
    if command.startswith('name '):
        new_name = command[5:].strip()
        if new_name:
            player.name = new_name
            # Save to account data
            if username in accounts:
                accounts[username]['char_name'] = new_name
                save_accounts(accounts)
    # Handle command; guard against None responses
    # Track room before command to detect movement
    prev_room = getattr(player, 'current_room', None)
    try:
        response = handle_command(command, player, world, accounts=accounts, save_accounts=save_accounts)
    except TypeError:
        # Backward compatibility with older signature
        response = handle_command(command, player, world)
    if not isinstance(response, str):
        response = ''
    # Detect if player was hit (simple example: response contains 'You were hit')
    if response and ('You were hit' in response or 'damage' in response):
        emit('player_hit')
    # Trigger crit visual when battle log includes CRIT!
    if response and ('CRIT!' in response):
        emit('player_crit')
    # Trigger heal visual when using Stimpack
    if response and ('Stimpack' in response or 'health and endurance surge' in response):
        emit('player_heal')
    if response:
        emit('message', {'data': response})
    # If player moved rooms, notify them and others in the new room
    new_room = getattr(player, 'current_room', None)
    if prev_room != new_room and new_room is not None:
        # Notify players in the previous room that this player left
        if prev_room is not None:
            for u, p in web_players.items():
                if u != username and getattr(p, 'current_room', None) == prev_room:
                    sid_prev = getattr(p, 'address', None)
                    if sid_prev:
                        socketio.emit('message', {'data': f"{player.name} leaves the room."}, room=sid_prev)
        # Notify this player of others present
        others = [u for u, p in web_players.items() if u != username and getattr(p, 'current_room', None) == new_room]
        if others:
            emit('message', {'data': f"You see {', '.join(others)} here."})
        # Notify other players in the room that this player arrived
        for u, p in web_players.items():
            if u != username and getattr(p, 'current_room', None) == new_room:
                sid_other = getattr(p, 'address', None)
                if sid_other:
                    socketio.emit('message', {'data': f"{player.name} enters the room."}, room=sid_other)
    # Detect if player was hit (simple example: response contains 'You were hit')
    if response and ('You were hit' in response or 'damage' in response):
        emit('player_hit')
    if response and ('CRIT!' in response):
        emit('player_crit')
    if response and ('Stimpack' in response or 'health and endurance surge' in response):
        emit('player_heal')
    # Send updated player info after each command
    emit('player_info', {
        'name': player.name,
        'race': player.race,
        'char_class': player.char_class,
        'level': player.level,
        'xp': player.xp,
        'xp_max': player.xp_max,
        'inventory': player.inventory,
        'equipment': getattr(player, 'equipment', {}),
        'hp': getattr(player, 'hp', 100),
        'energy': getattr(player, 'energy', 100),
        'endurance': getattr(player, 'endurance', 100),
        'willpower': getattr(player, 'willpower', 100),
        'strength': getattr(player, 'strength', 10),
        'tech': getattr(player, 'tech', 10),
        'speed': getattr(player, 'speed', 10),
        'abilities': getattr(player, 'abilities', []),
        'effects': [
            ('Red Eye', '+10% Attack') if getattr(player, 'attack_boost', 0) > 0 else None,
            ('Neon Blade', '+3 Atk, 15% Crit') if getattr(player, 'equipment', {}).get('weapon') == 'Neon Blade' else None
        ],
        'current_room': player.current_room,
        'rooms': world.rooms,
        'attack': player.get_attack() if hasattr(player, 'get_attack') else getattr(player, 'strength', 10),
        'attack_boost': getattr(player, 'attack_boost', 0),
        'fight_opponent': getattr(player, 'fight_opponent', None),
        'fight_hp': getattr(player, 'fight_hp', None),
        'room_info': {
            'name': player.current_room,
            'description': world.rooms[player.current_room]['description'],
            'exits': world.rooms[player.current_room]['exits'],
            'items': getattr(player, 'room_items', []),
            'npcs': world.get_npcs(player.current_room),
            'mobs': world.get_mobs_in_room(player.current_room)
        },
        # Global rule: enable regen for all players when not in battle
        'regen_enabled': (regen_enabled and not _is_in_fight(player))
    })
    # Persist progression (XP, Level) after each command
    if username in accounts:
        accounts[username]['xp'] = getattr(player, 'xp', accounts[username].get('xp', 0))
        accounts[username]['level'] = getattr(player, 'level', accounts[username].get('level', 1))
        accounts[username]['xp_max'] = getattr(player, 'xp_max', accounts[username].get('xp_max', 100))
        # Persist equipment (e.g., after equip/unequip/use commands)
        accounts[username]['equipment'] = dict(getattr(player, 'equipment', {}))
        accounts[username]['credits'] = int(getattr(player, 'credits', accounts[username].get('credits', 0)))
        accounts[username]['inventory'] = list(getattr(player, 'inventory', accounts[username].get('inventory', [])))
        accounts[username]['current_room'] = getattr(player, 'current_room', accounts[username].get('current_room', world.start_room))
        for attr in ('hp', 'energy', 'endurance', 'willpower'):
            accounts[username][attr] = int(getattr(player, attr, accounts[username].get(attr, 100)))
        try:
            save_accounts(accounts)
        except Exception:
            pass

if __name__ == '__main__':
    # Start background loops and run the development server
    _start_background_loops_once()
    socketio.run(app, host='0.0.0.0', port=5000)
