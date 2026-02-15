import socket
import threading
from game.commands import handle_command
from game.player import Player
from game.world import World


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
        client_sock.sendall(b"Welcome to the MUD!\n")
        while True:
            try:
                data = client_sock.recv(1024)
                if not data:
                    break
                command = data.decode().strip()
                response = handle_command(command, player, self.world)
                client_sock.sendall((response + '\n').encode())
            except Exception as e:
                print(f"Error: {e}")
                break
        client_sock.close()
        del self.clients[client_sock]
