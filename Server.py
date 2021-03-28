import socket
import threading
import logging

logging.basicConfig(filename="server.log", filemode="w", format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

class server():
    def __init__(self, config):
        self.host = config["host"]
        self.port = int(config["port"])
        self.users = {}

        # Setting up Main Server Socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))

        logging.info("Host : " + config["host"])
        logging.info("Port : " + str(config["port"]))

        # Listening for incoming connection requests
        self.listen()


    def listen(self):
        while (True):
            self.socket.listen()

            # accept a connection
            conn, addr = self.socket.accept()

            # Assign a new thread to a connection
            logging.info("Creating New Thread")
            threading.Thread(target=self.interact, args=(conn,)).start()


    def interact(self, conn):

        # get the username
        username = str(conn.recv(1024).decode('utf-8'))
        logging.info("Connect to " + username)

        self.users[username] = conn

        # Recieving Incoming Messages 
        while (True):
            data = str(conn.recv(1024).decode('utf-8'))
            logging.info("Recieved " + data)
            if (data == "exit"):
                break

            # Sending those messages to all users
            for c in self.users.values():
                c.send(data.encode('utf-8'))
        
        logging.info("Sending exit to " + username)
        conn.send("exit".encode('utf-8'))

        logging.info("Closing " + username)
        conn.close()


def Read_Config(filepath):
    config = {}
    with open(filepath, "r") as file:
        for line in file:
            line = line.split("=")
            config[line[0].strip()] = line[1].strip()
    
    return config


if (__name__ == "__main__"):
    config = Read_Config('.config')

    server(config)