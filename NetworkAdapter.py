import socket
import pickle
from Player import Player


class Network:
    """
    This class handles the socket, input, and game state.
    """
    def __init__(self, server_ip, server_port):
        self.state = []
        self.player_id = 0
        self.player = None
        self.players = []
        self.ready = False
        self.fail = False
        self.connection_status = "connecting"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server = server_ip
        self.port = int(server_port)
        self.server_addr = (self.server, self.port)
        self.MAX_DGRAM_SIZE = 4096

    # init a connection to the server
    def connect(self):
        payload = {
            "status": "connecting"
        }
        try:
            self.socket.sendto(pickle.dumps(payload), self.server_addr)
            data = pickle.loads(self.socket.recvfrom(self.MAX_DGRAM_SIZE)[0])

            if data.get("status") == "establishing":
                self.socket.sendto(pickle.dumps({"status": "validated"}), self.server_addr)
                init_state = pickle.loads(self.socket.recvfrom(self.MAX_DGRAM_SIZE)[0])
                self.process_payload(init_state)
            if data.get("status") == "max_connection":
                self.fail = True
            else:
                return
        except socket.error:
            print(socket.error)
            self.fail = True

    def disconnect(self):
        self.connection_status = "disconnect"
        self.ready = False
        print(f"client is disconnecting")
        self.socket.sendto(pickle.dumps({"status": "disconnect"}), self.server_addr)
        return

    # send player information to the server, return a new player state.
    # only works when connected to the server.
    def send(self, data):
        try:
            self.socket.sendto(pickle.dumps(data), self.server_addr)
            self.process_payload(pickle.loads(self.socket.recvfrom(self.MAX_DGRAM_SIZE)[0]))
        except socket.error:
            print(socket.error)

    def process_payload(self, payload):
        if payload.get("status") == "max_connection":
            print("server full, cannot connect")
            return
        elif payload.get("status") == "connected" and self.connection_status == "connecting":
            self.connection_status = "connected"
            if not self.ready:
                self.player_id = int(payload.get("player_id"))
                print(f"player id: {self.player_id}")
                self.players = payload.get("player_states")
                self.player = self.players[self.player_id]
                self.ready = True
                return
        elif payload.get("status") == "connected":
            self.players = payload.get("player_states")

    def move(self, direction):
        payload = {
            "status": "connected",
            "command": direction
        }
        self.send(payload)

    def get_players(self):
        return self.players

