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

class MudServer:
    def __init__(self, host='0.0.0.0', port=4000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.world = World()

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"MUD server started on {self.host}:{self.port}")
        while True:
            client_sock, addr = self.server_socket.accept()
            player = Player(addr, self.world.start_room)
            self.clients[client_sock] = player
            threading.Thread(target=self.handle_client, args=(client_sock,)).start()

    def handle_client(self, client_sock):
        player = self.clients[client_sock]

        def send_text(text: str):
            if not text:
                return

            style = OUTPUT_STYLE
            if style not in ('char', 'line'):
                style = 'char'

            if style == 'char':
                delay = CHAR_DELAY_SEC
                if delay and delay > 0:
                    # Typewriter: send per-character so clients display incremental output.
                    for ch in text:
                        client_sock.sendall(ch.encode(errors='replace'))
                        time.sleep(delay)
                else:
                    client_sock.sendall(text.encode(errors='replace'))
                return

            # style == 'line'
            delay = LINE_DELAY_SEC
            if delay and delay > 0:
                for line in text.splitlines(keepends=True) or [text]:
                    client_sock.sendall(line.encode(errors='replace'))
                    time.sleep(delay)
            else:
                client_sock.sendall(text.encode(errors='replace'))

        send_text("Welcome to the MUD!\n")
        while True:
            try:
                data = client_sock.recv(1024)
                if not data:
                    break
                command = data.decode().strip()
                response = handle_command(command, player, self.world)
                send_text(response + '\n')
            except Exception as e:
                print(f"Error: {e}")
                break
        client_sock.close()
        del self.clients[client_sock]
