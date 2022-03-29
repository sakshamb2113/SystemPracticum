import socket
import pickle
import threading
import fcntl, os
import time
from Player import Player

class GameSocket:
    
    MAX_CLIENTS = 4
    GAME_SIZE = (500, 500)
    TIMEOUT_SECONDS = 4
    PORT = None
    AVAILABLE = False

    def __init__(self, ip, port):
        print(ip, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        fcntl.fcntl(self.socket, fcntl.F_SETFL, os.O_NONBLOCK)
        self.PORT = port
        self.AVAILABLE = True
        try:
            self.socket.bind((ip, port))
        except socket.error as e:
            print(e)
        self.players = []
        self.clients_addr = []
        self.state_lock = threading.Lock()
        self.total_players = 0
        self.clients_time = []

        for i in range(0, self.MAX_CLIENTS):
            self.players.append(None)
            self.clients_addr.append(None)
            self.clients_time.append(None)
    
    def stop(self):
        self.state_lock.acquire()
        self.running_state = False
        self.state_lock.release()

    def incoming_conn_listener(self):
        while self.running_state:
            # "entry point" for all incoming requests
            try :
                data, addr = self.socket.recvfrom(4096)
            except socket.error as e:
                continue
            client_status = pickle.loads(data)
            # verify that the client is sending the correct information
            if type(client_status) is dict:
                self.process_payload(client_status, addr)

    def process_payload(self, data, addr):
        # if the server is full, send back that message and disconnect.
        if self.total_players >= self.MAX_CLIENTS:
            limit_message = {"status": "max_connection"}
            self.socket.sendto(pickle.dumps(limit_message), addr)
            return

        status = data.get("status")

        # initiate a new request and validate handshake
        if addr not in self.clients_addr:
            if status == "connecting":
                self.socket.sendto(pickle.dumps({"status": "establishing"}), addr)
            elif status == "validated":
                self.establish_connection(data, addr)
            return

        # when the client sends a clean disconnect request, remove them from the list
        if status == "disconnect":
            self.state_lock.acquire()
            self.disconnect(addr)
            self.state_lock.release()
            return

        # each player id is simply based on when they connected
        # ex 1st connection = player 1
        player_id = int(self.clients_addr.index(addr))
        self.process_state(data.get("command"), player_id)

        # the data sent to the client for processing
        payload = {
            "status": "connected",
            "player_id": player_id,
            "player_states": self.filter_players(self.players)
        }

        # there can only be one packet sent at a time from one socket.
        self.socket.sendto(pickle.dumps(payload), addr)

        # mark the last time seen in the client, to be compared by the timeout thread
        self.clients_time[player_id] = time.time_ns()

    # get a predefined color for each player based on id
    def get_color(self, index):
        colors = [(255, 255, 255), (100, 100, 150), (100, 150, 100), (150, 100, 100)]
        return colors[index]

    def establish_connection(self, data, addr):
        self.state_lock.acquire()
        player_pos = self.get_open_slot()
        self.clients_addr[player_pos] = (addr)
        player_id = player_pos
        self.players[player_pos] = Player(50, 50, 30, 30, self.get_color(player_id))
        self.clients_time[player_pos] = time.time_ns()
        self.total_players += 1
        self.state_lock.release()

        payload = {
            "status": "connected",
            "player_id": player_id,
            "player_states": self.filter_players(self.players)
        }

        # send the player the information upon initial connect
        print(f"{addr} connected as player {player_id}")
        self.socket.sendto(pickle.dumps(payload), addr)
        return
    
    def check_timeout(self):
        while True:
            self.state_lock.acquire()
            current = time.time_ns()
            for i in range(len(self.clients_time)):
                if self.clients_time[i] is not None:
                    if current - self.clients_time[i] > self.TIMEOUT_SECONDS * 1000000000:
                        print(f"connection timeout: {self.clients_addr[i]}")
                        self.disconnect(self.clients_addr[i])
            self.state_lock.release()
            time.sleep(self.TIMEOUT_SECONDS)

    def start_room(self):
        self.AVAILABLE = False
        print("Room Started at port ", self.PORT)
        self.running_state = True

        timeout_thread = threading.Thread(target=self.check_timeout, daemon=True)
        timeout_thread.start()
        print("server init complete. waiting for connection...")
        # blocking method, only stops when the kill command is given.
        self.incoming_conn_listener()
        print("Room Closed at Port ", self.PORT)

        self.AVAILABLE = True

    def filter_players(self, player_list):
        return list(filter(None, player_list))
    
    def get_open_slot(self):
        return self.clients_addr.index(None)

    def process_state(self, command, player_id):
        self.state_lock.acquire(blocking=True)
        self.players[player_id].move(command, self.GAME_SIZE)
        self.state_lock.release()
    
    def disconnect(self, addr):
        index = self.clients_addr.index(addr)
        print(f"player {index} disconnected")
        self.clients_addr[index] = None
        self.players[index] = None
        self.clients_time[index] = None
        self.total_players -= 1

if __name__ == "__main__":
    main()
