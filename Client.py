import logging
import socket
import threading

from protocols import protocol

logging.basicConfig(
    filename="client.log",
    filemode="w",
    format="%(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)


class client:
    def __init__(self):
        config = Read_Config(".config")
        self.host = config["host"]
        self.port = int(config["port"])
        self.server = (self.host, self.port)
        self.username = "UNKNOWN"
        self.__lock__ = threading.Lock()

    # Establishing Connection to Server
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.server)

        logging.info("Connected to Server " + self.host + ":" + str(self.port))

    # Sending username to Server
    def setUsername(self, username):
        msg = self.__wrap(protocol.SETUSERNAME, username)
        self.socket.send(msg)
        self.username = username

        logging.info("Username Set To " + username)

    # Getting Messages from Server
    def getMesseges(self):

        msg = self.socket.recv(1024).decode("utf-8")
        logging.info("Recieved " + msg)

        self.socket.send(self.__wrap(protocol.ACKNOLEDGEMENT, self.username))
        logging.info("Sent Ack")

        return self.__parse(msg)

    # Sending Message to Server
    def sendCommands(self, header, payload=""):
        msg = self.__wrap(header, payload)

        logging.info("Sending " + str(msg.decode("utf-8")))

        self.socket.send(msg)

    # Parsing messages
    def __parse(self, msg):
        header = msg[0:8]
        sender = msg[8:30].rstrip("_")
        payload = msg[34:]

        return (header, sender, payload)

    # Wrapping Messages
    def __wrap(self, header, payload):
        msg = (
            header
            + self.username.ljust(22, "_")
            + str(len(payload)).rjust(4, "0")
            + payload
        )

        return msg.encode("utf-8")

    # Closing Connection
    def close(self):
        self.socket.close()
        logging.info("Connection Closed")


def Read_Config(filepath):
    config = {}
    with open(filepath, "r") as file:
        for line in file:
            line = line.split("=")
            config[line[0].strip()] = line[1].strip()

    return config


if __name__ == "__main__":
    config = Read_Config(".config")

    client(config)
