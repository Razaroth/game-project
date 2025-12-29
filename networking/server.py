import socket
import threading
import os
import time
import json
from game.commands import handle_command
from game.player import Player
from game.world import World

try:
    from werkzeug.security import check_password_hash, generate_password_hash
except Exception:  # pragma: no cover
    check_password_hash = None
    generate_password_hash = None


ACCOUNTS_FILE = os.path.join('data', 'accounts.json')
_ACCOUNTS_LOCK = threading.Lock()


def _load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    try:
        with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return {}

    # Normalize legacy formats to dict form: {password: <hash|plain>, ...}
    changed = False
    for user, info in list(data.items()):
        if isinstance(info, str):
            pwd = info
            # Hash plaintext when possible.
            if generate_password_hash is not None:
                try:
                    if not any(str(pwd).startswith(prefix) for prefix in ('scrypt:', 'pbkdf2:', 'argon2:', 'sha256$')):
                        pwd = generate_password_hash(pwd)
                        changed = True
                except Exception:
                    pass
            data[user] = {
                'password': pwd,
                'email': '',
                'verified': False,
                'race': None,
                'char_class': None,
                'credits': 100,
            }
            changed = True
        elif isinstance(info, dict):
            if 'password' not in info:
                info['password'] = ''
                changed = True
            if 'credits' not in info:
                info['credits'] = 100
                changed = True
        else:
            data[user] = {'password': '', 'credits': 100}
            changed = True

    if changed:
        try:
            _save_accounts(data)
        except Exception:
            pass

    return data


def _save_accounts(accounts):
    os.makedirs(os.path.dirname(ACCOUNTS_FILE) or '.', exist_ok=True)
    with _ACCOUNTS_LOCK:
        tmp_path = ACCOUNTS_FILE + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(accounts, f)
        try:
            os.replace(tmp_path, ACCOUNTS_FILE)
        except Exception:
            with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(accounts, f)


def _verify_password(stored, provided) -> bool:
    if stored is None:
        return False
    stored = str(stored)
    provided = str(provided or '')
    if not provided:
        return False
    if check_password_hash is not None:
        try:
            # check_password_hash handles werkzeug-hashed formats.
            if any(stored.startswith(prefix) for prefix in ('scrypt:', 'pbkdf2:', 'argon2:', 'sha256$')):
                return bool(check_password_hash(stored, provided))
        except Exception:
            pass
    # Fallback: plaintext compare (legacy)
    return stored == provided


def _persist_player_state(accounts, username, player, world):
    if not username or player is None:
        return
    if username not in accounts or not isinstance(accounts.get(username), dict):
        accounts[username] = {'password': '', 'credits': 100}
    acc = accounts[username]

    room = getattr(player, 'current_room', world.start_room)
    # If player is inside a mission instance, store the entry alley when possible.
    try:
        inst = world.get_instance_for_player(player) if hasattr(world, 'get_instance_for_player') else None
        if hasattr(world, 'is_instance_room') and world.is_instance_room(room) and inst:
            room = inst.get('entry_room') or world.start_room
    except Exception:
        pass

    acc['current_room'] = room
    acc['inventory'] = list(getattr(player, 'inventory', acc.get('inventory', [])) or [])
    acc['equipment'] = dict(getattr(player, 'equipment', acc.get('equipment', {})) or {})
    acc['quests'] = dict(getattr(player, 'quests', acc.get('quests', {})) or {})
    acc['credits'] = int(getattr(player, 'credits', acc.get('credits', 0)) or 0)
    acc['xp'] = int(getattr(player, 'xp', acc.get('xp', 0)) or 0)
    acc['level'] = int(getattr(player, 'level', acc.get('level', 1)) or 1)
    acc['xp_max'] = int(getattr(player, 'xp_max', acc.get('xp_max', 100)) or 100)

    for attr in ('hp', 'energy', 'endurance', 'willpower'):
        try:
            acc[attr] = int(getattr(player, attr, acc.get(attr, 100)) or 0)
        except Exception:
            pass
    for attr in ('strength', 'tech', 'speed'):
        try:
            acc[attr] = int(getattr(player, attr, acc.get(attr, 10)) or 0)
        except Exception:
            pass

    if getattr(player, 'name', None):
        acc['char_name'] = getattr(player, 'name')
    if getattr(player, 'race', None) is not None:
        acc['race'] = getattr(player, 'race')
    if getattr(player, 'char_class', None) is not None:
        acc['char_class'] = getattr(player, 'char_class')

    _save_accounts(accounts)


def _player_from_account(addr, username, acc, world):
    player = Player(addr, world.start_room)
    try:
        player.username = username
    except Exception:
        pass
    player.name = (acc.get('char_name') if isinstance(acc, dict) else None) or username
    if isinstance(acc, dict):
        player.race = acc.get('race')
        player.char_class = acc.get('char_class')
        try:
            if hasattr(player, 'apply_race_class'):
                player.apply_race_class()
        except Exception:
            pass
        if isinstance(acc.get('equipment'), dict):
            try:
                player.equipment.update(acc.get('equipment'))
            except Exception:
                pass
        if isinstance(acc.get('inventory'), list):
            try:
                player.inventory = list(acc.get('inventory'))
            except Exception:
                pass
        if isinstance(acc.get('quests'), dict):
            try:
                player.quests = dict(acc.get('quests'))
            except Exception:
                pass
        if isinstance(acc.get('current_room'), str) and acc.get('current_room') in world.rooms:
            player.current_room = acc.get('current_room')
        for key in ('credits', 'xp', 'level', 'xp_max'):
            if key in acc:
                try:
                    setattr(player, key, int(acc.get(key)))
                except Exception:
                    pass
        for attr in ('hp', 'energy', 'endurance', 'willpower', 'strength', 'tech', 'speed'):
            if attr in acc:
                try:
                    setattr(player, attr, int(acc.get(attr)))
                except Exception:
                    pass
    return player


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return float(default)


# Output pacing for console/telnet clients.
#
# - MUD_OUTPUT_STYLE: 'char' (typewriter) or 'line'
# - MUD_CHAR_DELAY_SEC: delay between characters (seconds)
# - MUD_LINE_DELAY_SEC: delay between lines (seconds)
#
# Back-compat:
# - MUD_TEXT_DELAY_SEC will be used as the char delay if MUD_CHAR_DELAY_SEC is unset.
OUTPUT_STYLE = (os.getenv('MUD_OUTPUT_STYLE', 'char') or 'char').strip().lower()
CHAR_DELAY_SEC = _safe_float(os.getenv('MUD_CHAR_DELAY_SEC', os.getenv('MUD_TEXT_DELAY_SEC', '0.03')), 0.03)
LINE_DELAY_SEC = _safe_float(os.getenv('MUD_LINE_DELAY_SEC', '0.10'), 0.10)


def _pluralize(name, count):
    if count == 1:
        return str(name)
    n = str(name)
    if n.endswith('s'):
        return n
    return n + 's'


def _send_paced(client_sock, text: str):
    if not text:
        return

    style = OUTPUT_STYLE
    if style not in ('char', 'line'):
        style = 'char'

    if style == 'char':
        delay = CHAR_DELAY_SEC
        if delay and delay > 0:
            for ch in text:
                client_sock.sendall(ch.encode(errors='replace'))
                time.sleep(delay)
        else:
            client_sock.sendall(text.encode(errors='replace'))
        return

    delay = LINE_DELAY_SEC
    if delay and delay > 0:
        for line in text.splitlines(keepends=True) or [text]:
            client_sock.sendall(line.encode(errors='replace'))
            time.sleep(delay)
    else:
        client_sock.sendall(text.encode(errors='replace'))

class MudServer:
    def __init__(self, host='0.0.0.0', port=4000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.world = World()
        self._lock = threading.Lock()
        self._roam_started = False
        self._accounts = _load_accounts()

    def _start_roaming_loop(self, interval_sec=3.0):
        if self._roam_started:
            return
        self._roam_started = True

        def loop():
            while True:
                try:
                    moves = self.world.tick_roaming() or []
                    entered_by_room = {}
                    for src, dst, mob_name in moves:
                        if not dst or not mob_name:
                            continue
                        entered_by_room.setdefault(dst, {})
                        entered_by_room[dst][mob_name] = entered_by_room[dst].get(mob_name, 0) + 1

                    now = time.time()
                    with self._lock:
                        for client_sock, player in list(self.clients.items()):
                            try:
                                # Timed buff expiry notifications.
                                if hasattr(player, 'refresh_timed_effects'):
                                    try:
                                        player.refresh_timed_effects(now=now)
                                    except Exception:
                                        pass
                                if hasattr(player, 'pop_notices'):
                                    try:
                                        for notice in (player.pop_notices() or []):
                                            if notice:
                                                _send_paced(client_sock, str(notice) + "\n")
                                    except Exception:
                                        pass

                                # Roaming mob announcements.
                                if not entered_by_room:
                                    continue
                                cur = getattr(player, 'current_room', None)
                                if cur not in entered_by_room:
                                    continue
                                parts = []
                                for mob_name, cnt in entered_by_room[cur].items():
                                    if int(cnt) == 1:
                                        parts.append(f"A {mob_name} enters the area.")
                                    else:
                                        parts.append(f"A gang of {int(cnt)} {_pluralize(mob_name, int(cnt))} enters the area.")
                                if parts:
                                    _send_paced(client_sock, "\n".join(parts) + "\n")
                            except Exception:
                                continue
                except Exception:
                    pass
                time.sleep(interval_sec)

        threading.Thread(target=loop, daemon=True).start()

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"MUD server started on {self.host}:{self.port}")

        # Start roaming enemies/gangs loop for console clients.
        self._start_roaming_loop(interval_sec=1.5)

        while True:
            client_sock, addr = self.server_socket.accept()
            player = Player(addr, self.world.start_room)
            with self._lock:
                self.clients[client_sock] = player
            threading.Thread(target=self.handle_client, args=(client_sock,)).start()

    def handle_client(self, client_sock):
        with self._lock:
            player = self.clients.get(client_sock)
        if player is None:
            return

        # Track login state for this connection
        authed_username = None

        _send_paced(client_sock, "Welcome to the MUD!\n")
        _send_paced(client_sock, "Tip: login <username> <password> to load/save your character.\n")
        while True:
            try:
                data = client_sock.recv(1024)
                if not data:
                    break
                command = data.decode().strip()

                # Optional login for persistence
                if command.lower().startswith('login '):
                    parts = command.split(maxsplit=2)
                    if len(parts) < 3:
                        _send_paced(client_sock, "Usage: login <username> <password>\n")
                        continue
                    u = parts[1].strip()
                    pw = parts[2]
                    with _ACCOUNTS_LOCK:
                        self._accounts = _load_accounts()
                        acc = self._accounts.get(u)
                    if not isinstance(acc, dict):
                        _send_paced(client_sock, "Unknown account. Use the web UI to register first.\n")
                        continue
                    if not _verify_password(acc.get('password'), pw):
                        _send_paced(client_sock, "Invalid username/password.\n")
                        continue

                    authed_username = u
                    player = _player_from_account(getattr(player, 'address', None), u, acc, self.world)
                    with self._lock:
                        self.clients[client_sock] = player

                    _send_paced(client_sock, f"Logged in as {u}.\n")
                    _send_paced(client_sock, self.world.describe_room(player.current_room, entering=True) + "\n")
                    continue

                # Normal command handling
                response = handle_command(command, player, self.world)
                _send_paced(client_sock, response + '\n')

                # Persist after each command if logged in
                if authed_username:
                    try:
                        _persist_player_state(self._accounts, authed_username, player, self.world)
                    except Exception:
                        pass

                # Flush any pending notices (e.g., buff expirations triggered by combat math).
                if hasattr(player, 'pop_notices'):
                    try:
                        for notice in (player.pop_notices() or []):
                            if notice:
                                _send_paced(client_sock, str(notice) + "\n")
                    except Exception:
                        pass
            except Exception as e:
                print(f"Error: {e}")
                break
        client_sock.close()
        with self._lock:
            self.clients.pop(client_sock, None)

        # Persist on disconnect if logged in
        if authed_username:
            try:
                _persist_player_state(self._accounts, authed_username, player, self.world)
            except Exception:
                pass
