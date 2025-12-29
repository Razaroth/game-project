import socket
import threading
import os
import time
from game.commands import handle_command
from game.player import Player
from game.world import World


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

                    if entered_by_room:
                        with self._lock:
                            for client_sock, player in list(self.clients.items()):
                                try:
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
        self._start_roaming_loop(interval_sec=3.0)

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

        _send_paced(client_sock, "Welcome to the MUD!\n")
        while True:
            try:
                data = client_sock.recv(1024)
                if not data:
                    break
                command = data.decode().strip()
                response = handle_command(command, player, self.world)
                _send_paced(client_sock, response + '\n')
            except Exception as e:
                print(f"Error: {e}")
                break
        client_sock.close()
        with self._lock:
            self.clients.pop(client_sock, None)
