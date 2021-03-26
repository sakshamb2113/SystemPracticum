import socket
import threading
import logging 

logging.basicConfig(filename="client.log", filemode="w", format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

class client:
    def __init__(self):
        config = Read_Config(".config")
        self.host = config["host"]
        self.port = int(config["port"])
        self.server = (self.host, self.port)
    
    # Establishing Connection to Server
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.server)
        
        logging.info("Connected to Server " + self.host + ":" + str(self.port))

    # Sending username to Server
    def setUsername(self, username):
        self.socket.send(username.encode("utf-8"))
        logging.info("Username Set To " + username)
    
    # Getting Messages from Server
    def getMesseges(self):
        msg = str(self.socket.recv(1024).decode('utf-8'))
        logging.info("Recieved " + msg)

        return msg

    # Sending Message to Server
    def sendCommands(self, msg):
        logging.info("Sending " + msg)
        self.socket.send(msg.encode("utf-8"))


def Read_Config(filepath):
    config = {}
    with open(filepath, "r") as file:
        for line in file:
            line = line.split("=")
            config[line[0].strip()] = line[1].strip()
    
    return config

if (__name__ == "__main__"):
    config = Read_Config('.config')

    client(config)
