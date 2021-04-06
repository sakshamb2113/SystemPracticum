import json
import logging
import socket
import threading

from protocols import protocol

logging.basicConfig(filename="server.log", filemode="w", format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

helpmsg  = "<br>----- HELP -----<br>"
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

class server():
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
        while (True):
            self.socket.listen()

            # accept a connection
            conn, addr = self.socket.accept()

            # Assign a new thread to a connection
            threading.Thread(target=self.interact, args=(conn,)).start()


    def sendMessageToRoom(self, room, msg):
        # Sending those messages to all users in currRoom
        for user in self.rooms[room]:
            self.users[user].send(msg)


    def joinRoom(self, usr, room):
        # Adding current user to the room
        self.rooms[room].append(usr)

        # Sending Response
        if (room != "lobby"):
            self.sendMessageToRoom(room, self.__wrap(protocol.UPDATE, "SERVER", usr + " has joined the room " + room))


    def leaveRoom(self, usr, room):
        # informing people that username has left there room
        if (room != "lobby"):
            self.sendMessageToRoom(room, self.__wrap(protocol.UPDATE, "SERVER", usr + " has left the room " + room))

        # Removing user from old room
        self.rooms[room].remove(usr)

        # if room gets empty then delete it
        if (len(self.rooms[room]) == 0 and room != "lobby"):
            self.rooms.pop(room)


    def interact(self, conn):
        logging.info("New Connection Established")

        # get the username
        header, sender, username = self.__parse(str(conn.recv(1024).decode('utf-8')))
        currRoom = "lobby"

        while (self.__checkUsername(username) == False):
            conn.send(self.__wrap(protocol.REJECT, "SERVER", "Username Invalid"))
            header, sender, username = self.__parse(str(conn.recv(1024).decode('utf-8')))
        
        conn.send(self.__wrap(protocol.ACCEPT, "SERVER", "UserName Set"))
        logging.info("User set to " + username)

        # Adding Username to the list of users and lobby
        self.users[username] = conn
        self.rooms[currRoom].append(username)

        # Sending Welcome Message from Server
        conn.send(self.__wrap(protocol.MESSAGE, "SERVER", "Welcome " + username + "!! Enter #help for the manual."))

        # Recieving Incoming Messages 
        while (True):
            msg = str(conn.recv(1024).decode('utf-8'))
            logging.info("Recieved " + msg)
            
            header, sender, payload = self.__parse(msg)

            if (header == protocol.EXIT):
                self.leaveRoom(username, currRoom)
                break

            elif (header == protocol.HELP):
                # Sending Help Message
                conn.send(self.__wrap(protocol.HELP, "SERVER", helpmsg))
            
            elif (header == protocol.MESSAGE):
                if (currRoom == "lobby"):
                    conn.send(self.__wrap(protocol.REJECT, "SERVER", "Join a room to send messages."))
                    continue
                
                self.sendMessageToRoom(currRoom, self.__wrap(protocol.MESSAGE, username, payload))

            elif (header == protocol.GETROOMLIST):
                roomList = list(self.rooms.keys())
                roomList.remove("lobby")

                # Sending room list
                conn.send(self.__wrap(protocol.ROOMLIST, "SERVER", json.dumps(roomList)))
            
            elif (header == protocol.CREATEROOM):
                
                if (payload == "lobby"):
                    logging.debug("New Room named lobby denied to " + sender)
                    conn.send(self.__wrap(protocol.REJECT, "SERVER", "lobby is an invalid room name. try something else"))
                
                elif payload in self.rooms.keys():
                    logging.debug("New Room with Same name as existing denied to " + sender)
                    conn.send(self.__wrap(protocol.REJECT, "SERVER", "Room name already taken."))
                
                elif (len(payload) > 20):
                    logging.debug("Room Name " + payload + " is too big. Denied " + sender) 
                    conn.send(self.__wrap(protocol.REJECT, "SERVER", "Room name too big, Max Name Size is 20 characters"))

                elif (len(payload) < 5):
                    logging.debug("Room Name " + payload + " is too small. Denied " + sender) 
                    conn.send(self.__wrap(protocol.REJECT, "SERVER", "Room name too small, Min Name Size is 5 characters"))

                else:
                    # Creating New Room
                    self.rooms[payload] = []

                    self.leaveRoom(username, currRoom)
                    currRoom = payload
                    self.joinRoom(username, currRoom)

            elif (header == protocol.JOINROOM):
                if (payload not in self.rooms.keys() or payload == "lobby"):
                    conn.send(self.__wrap(protocol.REJECT, "SERVER", "Please Enter a valid room-name"))
                    logging.debug("Incorrect Room Name : " + payload + " by " + sender)

                elif (currRoom == payload):
                    conn.send(self.__wrap(protocol.REJECT, "SERVER", "Already in the mentioned room"))

                else:
                    self.leaveRoom(username, currRoom)
                    currRoom = payload
                    self.joinRoom(username, currRoom)

            elif (header == protocol.LEAVEROOM):
                if (currRoom == "lobby"):
                    conn.send(self.__wrap(protocol.REJECT, "SERVER", "Not in any Room"))

                else:
                    self.leaveRoom(username, currRoom)
                    currRoom = "lobby"
                    self.joinRoom(username, currRoom)

            else: 
                conn.send(self.__wrap(protocol.REJECT, "SERVER", "Unknown Header: " + header))
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