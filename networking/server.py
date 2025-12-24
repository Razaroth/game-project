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


# Delay (seconds) between *lines* when sending text to console clients.
# Set env var MUD_LINE_DELAY_SEC=0 to disable.
# Back-compat: if MUD_LINE_DELAY_SEC is unset, fall back to MUD_TEXT_DELAY_SEC.
LINE_DELAY_SEC = _safe_float(os.getenv('MUD_LINE_DELAY_SEC', os.getenv('MUD_TEXT_DELAY_SEC', '1.00')), 1.00)

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
            if LINE_DELAY_SEC and LINE_DELAY_SEC > 0:
                # Send per-line for smoother pacing than per-character.
                for line in text.splitlines(keepends=True) or [text]:
                    client_sock.sendall(line.encode(errors='replace'))
                    time.sleep(LINE_DELAY_SEC)
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
