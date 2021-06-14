import json
import logging
import socket
from time import sleep
import threading

from protocols import protocol
from GameServer import runGameServer

gameport = 9562

logging.basicConfig(
    filename="server.log",
    filemode="w",
    format="%(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)

helpmsg = "<br>----- HELP -----<br>"
helpmsg += "To Send a Message just enter in the provided input box and hit send.<br>"
helpmsg += "To run a command prefix it with a '#' sign just like you did for help.<br>"
helpmsg += "------- List Commands -------<br>"
helpmsg += "#help : get the man page.<br>"
helpmsg += "#getrooms : get the list of rooms with users.<br>"
helpmsg += "#joinroom roomname : Joins the room with the given name is it exists.<br>"
helpmsg += "#createroom roomname : Create a new room with the specified name (if possible) and joins it.<br>"
helpmsg += "#exitroom : exits the current room and goes back into the lobby."
helpmsg += "----- END List Commands -----<br>"
helpmsg += "--- END HELP ---<br>"


class user:
    def __init__(self, username, conn, room):
        self.__conn__ = conn
        self.__lock__ = threading.Lock()
        self.name = username
        self.room = room
        self.__ack = False

    def __str__(self):
        return f"User({self.name})"

    def toggleAck(self):
        self.__ack = True

    def send(self, header, sender, payload=""):
        msg = _wrap(header, sender, payload)
        Rheader, Rsender, Rpayload = " ", " ", " "

        logging.debug("Acquiring lock on " + self.name + ".send for  " + msg)
        self.__lock__.acquire()
        logging.debug("Acquired lock on " + self.name + ".send for  " + msg)

        logging.info("Sending to " + self.name + " : \t\t" + msg)
        self.__conn__.send(msg.encode("utf-8"))
        logging.info("Waiting for ack to " + msg)

        while self.__ack == False:
            sleep(0.01)

        self.__ack = False

        self.__lock__.release()
        logging.debug("Released lock on " + self.name + ".send for  " + msg)

        logging.info("Ack Recieved for " + msg)

    def recieve(self):
        msg = str(self.__conn__.recv(1024).decode("utf-8"))

        logging.info("Recieved : \t\t\t\t" + msg)

        return _parse(msg)


class server:
    def __init__(self, config):
        self.host = config["host"]
        self.port = int(config["port"])
        self.users = {}
        self.rooms = {"lobby": []}

        # Setting up Main Server Socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))

        logging.info("Host : " + config["host"])
        logging.info("Port : " + str(config["port"]))

        # Listening for incoming connection requests
        self.listen()

    def listen(self):
        while True:
            self.socket.listen()

            # accept a connection
            conn, addr = self.socket.accept()

            # Assign a new thread to a connection
            threading.Thread(target=self.interact, args=(conn,)).start()

    def sendMessageToRoom(self, room, header, sender, payload=""):
        # Sending those messages to all users in currRoom
        for user in self.rooms[room]:
            self.users[user].send(header, sender, payload)

    def sendMessageToUser(self, user, header, sender, payload=""):
        # Sending the message to user
        self.users[user].send(header, sender, payload)

    def joinRoom(self, usr, room):
        logging.debug(usr + " joining room " + room)
        # Adding current user to the room
        self.rooms[room].append(usr)
        self.users[usr].room = room

        # Sending Response
        if room != "lobby":
            self.sendMessageToRoom(
                room, protocol.UPDATE, "SERVER", usr + " has joined the room " + room
            )

    def leaveRoom(self, usr):
        room = self.users[usr].room

        logging.debug(usr + " leaving room " + room)
        # informing people that username has left there room
        if room != "lobby":
            self.sendMessageToRoom(
                room, protocol.UPDATE, "SERVER", usr + " has left the room " + room
            )

        # Removing user from old room
        self.rooms[room].remove(usr)
        self.users[usr].room = "-"

        # if room gets empty then delete it
        if len(self.rooms[room]) == 0 and room != "lobby":
            logging.debug("Deleting Room " + room)
            self.rooms.pop(room)

    def MESSAGE(self, username, payload):
        currRoom = self.users[username].room
        if currRoom == "lobby":
            self.sendMessageToUser(
                username, protocol.REJECT, "SERVER", "Join a room to send messages."
            )
        else:
            self.sendMessageToRoom(currRoom, protocol.MESSAGE, username, payload)

    def GETROOMLIST(self, username):
        roomList = list(self.rooms.keys())
        roomList.remove("lobby")

        # Sending room list
        self.sendMessageToUser(
            username, protocol.ROOMLIST, "SERVER", json.dumps(roomList)
        )

    def CREATEROOM(self, username, payload):
        sender=username
        if payload == "lobby":
            logging.debug("New Room named lobby denied to " + sender)
            self.sendMessageToUser(
                username,
                protocol.REJECT,
                "SERVER",
                "lobby is an invalid room name. try something else",
            )

        elif payload in self.rooms.keys():
            logging.debug("New Room with Same name as existing denied to " + sender)
            self.sendMessageToUser(
                username, protocol.REJECT, "SERVER", "Room name already taken."
            )

        elif len(payload) > 20:
            logging.debug("Room Name " + payload + " is too big. Denied " + sender)
            self.sendMessageToUser(
                username,
                protocol.REJECT,
                "SERVER",
                "Room name too big, Max Name Size is 20 characters",
            )

        elif len(payload) < 5:
            logging.debug("Room Name " + payload + " is too small. Denied " + sender)
            self.sendMessageToUser(
                username,
                protocol.REJECT,
                "SERVER",
                "Room name too small, Min Name Size is 5 characters",
            )

        else:
            # Creating New Room
            self.rooms[payload] = []

            self.leaveRoom(username)
            self.joinRoom(username, payload)

    def JOINROOM(self, username, payload):
        currRoom = self.users[username].room

        if payload not in self.rooms.keys() or payload == "lobby":
            self.sendMessageToUser(
                username, protocol.REJECT, "SERVER", "Please Enter a valid room-name"
            )
            logging.debug("Incorrect Room Name : " + payload + " by " + sender)

        elif currRoom == payload:
            self.sendMessageToUser(
                username, protocol.REJECT, "SERVER", "Already in the mentioned room"
            )

        else:
            self.leaveRoom(username)
            self.joinRoom(username, payload)

    def LEAVEROOM(self, username):
        currRoom = self.users[username].room

        if currRoom == "lobby":
            self.sendMessageToUser(
                username, protocol.REJECT, "SERVER", "Not in any Room"
            )

        else:
            self.leaveRoom(username)
            currRoom = "lobby"
            self.joinRoom(username, currRoom)

    def CHALLENGE(self, username, payload):
        if payload not in self.users.keys():
            self.sendMessageToUser(username, protocol.MESSAGE, "SERVER", "No User with given username")
            return

        self.sendMessageToUser(payload, protocol.CHALLENGE_RECIEVED, username)

    def CHALLENGE_ACCEPTED(self, username, payload):
        self.sendMessageToUser(payload, protocol.CHALLENGE_ACCEPTED, username)

        self.START_GAME_SERVER([username, payload])

    def CHALLENGE_REJECTED(self, username, payload):
        self.sendMessageToUser(payload, protocol.CHALLENGE_REJECTED, username)

    def START_GAME_SERVER(self, users):
        threading.Thread(target=runGameServer, args=(gameport,)).start()

        for user in users:
            self.sendMessageToUser(user, protocol.CONNECTGAME, "SERVER", str(gameport))

    def UNKNOWNHEADER(self, username):
        self.sendMessageToUser(
            username, protocol.REJECT, "SERVER", "Unknown Header: " + header
        )
        logging.debug("Unknown header Recieved")

    def interact(self, conn):
        logging.info("New Connection Established")

        # get the username
        header, sender, username = _parse(conn.recv(1024).decode("utf-8"))

        while self.__checkUsername(username) == False:
            conn.send(
                _wrap(protocol.REJECT, "SERVER", "Username Invalid").encode("utf-8")
            )

            # Recieving Acknoledgement for REJECT
            Rheader, Rsender, Rpayload = _parse(conn.recv(1024).decode("utf-8"))

            # Recieving new username
            header, sender, username = _parse(conn.recv(1024).decode("utf-8"))

        conn.send(_wrap(protocol.ACCEPT, "SERVER", "UserName Set").encode("utf-8"))

        # Recieving Acknoledgement for ACCEPT
        Rheader, Rsender, Rpayload = _parse(conn.recv(1024).decode("utf-8"))

        logging.info("User set to " + username)

        # Adding Username to the list of users and lobby
        self.users[username] = user(username, conn, "-")
        self.joinRoom(username, "lobby")

        # Sending Welcome Message from Server
        threading.Thread(
            target=lambda username: self.sendMessageToUser(
                username,
                protocol.MESSAGE,
                "SERVER",
                "Welcome " + username + "!! Enter #help for the manual.",
            ),
            args=(username,),
        ).start()

        # Recieving Incoming Messages
        while True:
            header, sender, payload = self.users[username].recieve()

            if header == protocol.EXIT:
                break

            elif header == protocol.HELP:
                # Sending Help Message
                threading.Thread(
                    target=lambda username: self.sendMessageToUser(
                        username, protocol.HELP, "SERVER", helpmsg
                    ),
                    args=(username,),
                ).start()

            elif header == protocol.MESSAGE:
                threading.Thread(target=self.MESSAGE, args=(username, payload)).start()

            elif header == protocol.GETROOMLIST:
                threading.Thread(target=self.GETROOMLIST, args=(username,)).start()

            elif header == protocol.CREATEROOM:
                threading.Thread(
                    target=self.CREATEROOM, args=(username, payload)
                ).start()

            elif header == protocol.JOINROOM:
                threading.Thread(target=self.JOINROOM, args=(username, payload)).start()

            elif header == protocol.LEAVEROOM:
                threading.Thread(target=self.LEAVEROOM, args=(username,)).start()

            elif header == protocol.ACKNOLEDGEMENT:
                self.users[username].toggleAck()

            elif header == protocol.CHALLENGE:
                threading.Thread(target=self.CHALLENGE, args=(username, payload)).start()

            elif header == protocol.CHALLENGE_ACCEPTED:
                threading.Thread(target=self.CHALLENGE_ACCEPTED, args=(username, payload)).start()

            elif header == protocol.CHALLENGE_REJECTED:
                threading.Thread(target=self.CHALLENGE_REJECTED, args=(username, payload)).start()

            else:
                threading.Thread(target=self.UNKNOWNHEADER, args=(username,)).start()

        currRoom = self.users[username].room

        threading.Thread(target=self.leaveRoom, args=(username,)).start()

        # Recieving Ack
        if (currRoom != "lobby"):
            header, sender, payload = self.users[username].recieve()
            self.users[username].toggleAck()

        logging.info("Sending exit to " + username)
        threading.Thread(
            target=lambda user: self.users[username].send(protocol.EXIT, "SERVER", ""),
            args=(username,),
        ).start()

        header, sender, payload = self.users[username].recieve()
        self.users[username].toggleAck()

        # Removing user for list
        x = self.users.pop(username)

        logging.info("Closing " + username)
        conn.close()

    def __checkUsername(self, usr):
        if usr == "":
            logging.debug("Empty Username")
            return False

        if len(usr) > 22:
            logging.debug("Username too big : " + usr)
            return False

        for ch in usr:
            if ch == "_":
                logging.debug("Username Contains _ : " + usr)
                return False

        if usr == "UNKNOWN" or usr == "SERVER":
            logging.debug("UNKNOWN and SERVER are reserved : " + usr)
            return False

        if usr in self.users.keys():
            logging.debug("Username already taken : ", usr)
            return False

        return True


def _wrap(header, sender, payload=""):
    packet = header + sender.ljust(22, "_") + str(len(payload)).rjust(4, "0") + payload

    return packet


# Parsing messages
def _parse(msg):
    header = msg[0:8]
    sender = msg[8:30].rstrip("_")
    payload = msg[34:]

    return (header, sender, payload)


def Read_Config(filepath):
    config = {}
    with open(filepath, "r") as file:
        for line in file:
            line = line.split("=")
            config[line[0].strip()] = line[1].strip()

    return config


if __name__ == "__main__":
    config = Read_Config(".config")

    server(config)
