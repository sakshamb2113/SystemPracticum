import socket
import threading
import logging 

logging.basicConfig(filename="client.log", filemode="w", format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

class client:
    def __init__(self, config):
        self.host = config["host"]
        self.port = int(config["port"])
        self.server = (self.host, self.port)
        
        # Connecting to Server
        self.connect()
        logging.info("Connected to Server " + self.host + ":" + str(self.port))

        # Sending username to Server
        username = input("Enter UserName : ")
        self.socket.send(username.encode("utf-8"))

        # Creating Individual Threads for listening to Server and to Sending msgs to Server
        threading.Thread(target=self.getMesseges).start()
        threading.Thread(target=self.sendCommands).start()
    
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.server)
    
    def getMesseges(self):
        while (True):
            msg = str(self.socket.recv(1024).decode('utf-8'))

            logging.info("Recieved " + msg)
            if (msg == "exit"):
                break

            print("Server > ", msg)
        
        logging.info("Ending getMesseges")

    def sendCommands(self):
        while(True):
            msg = input("__YOU__>")
            logging.info("Sending " + msg)
            self.socket.send(msg.encode("utf-8"))
            if (msg == "exit"):
                break
        
        logging.info("Ending sendCommands")

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
