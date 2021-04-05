import socket
import threading
import logging
from protocols import protocol

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
            threading.Thread(target=self.interact, args=(conn,)).start()


    def interact(self, conn):
        logging.info("New Connection Established")

        # get the username
        header, sender, username = self.__parse(str(conn.recv(1024).decode('utf-8')))

        while (self.__checkUsername(username) == False):
            conn.send(self.__wrap(protocol.REJECT, "SERVER", "Username Invalid"))
            header, sender, username = self.__parse(str(conn.recv(1024).decode('utf-8')))
        
        conn.send(self.__wrap(protocol.ACCEPT, "SERVER", "UserName Set"))
        logging.info("User set to " + username)

        # Adding Username to the list of users
        self.users[username] = conn

        # Recieving Incoming Messages 
        while (True):
            msg = str(conn.recv(1024).decode('utf-8'))
            logging.info("Recieved " + msg)
            
            header, sender, payload = self.__parse(msg)
            if (header == protocol.EXIT):
                break

            elif (header == protocol.MESSAGE):
                # Sending those messages to all users
                for c in self.users.values():
                    c.send(self.__wrap(protocol.MESSAGE, sender, payload))
            
            else: 
                logging.debug("Unknown header Recieved")
        
        logging.info("Sending exit to " + username)
        conn.send(self.__wrap(protocol.EXIT, "SERVER"))

        # Removing user for list
        x = self.users.pop(username)

        logging.info("Closing " + username)
        conn.close()

    def __checkUsername(self, usr):
        if (usr == ""):
            logging.debug("Empty Username")
            return False
        
        if (len(usr) > 22):
            logging.debug("Username too big : " + usr)
            return False
        
        for ch in usr:
            if (ch == "_"):
                logging.debug("Username Contains _ : " + usr)
                return False
        
        if (usr == "UNKNOWN" or usr == "SERVER"):
            logging.debug("UNKNOWN and SERVER are reserved : " + usr)
            return False
        
        if usr in self.users.keys():
            logging.debug("Username already taken : ", usr)
            return False
        
        return True
    
    def __wrap(self ,header, sender, payload = ""):
        packet = header + sender.ljust(22, "_") + str(len(payload)).rjust(4, "0") + payload

        return packet.encode('utf-8')

    # Parsing messages
    def __parse(self, msg):
        header = msg[0:8]
        sender = msg[8:30].rstrip('_')
        payload = msg[34:]

        return (header, sender, payload)


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