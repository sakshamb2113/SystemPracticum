import json
import sys
import threading

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Client import client
from protocols import protocol


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.client = client()

        self.setWindowTitle("Gaminal")
        self.setFixedSize(600, 600)

        self.SetupUI()

        self.dialog = self.connectDialog()
        self.dialog.exec_()

    # Establishing Connection
    def connect(self):
        self.client.connect()

        self.dialog.close()
        self.dialog = self.usernameDialog()
        self.dialog.exec_()

    # get Username Dialog
    def usernameDialog(self):
        dialog = ModalDialog(self)
        dialog.setFixedSize(400, 200)

        usernameInput = QLineEdit(dialog)
        usernameInput.setPlaceholderText("Username...")
        button = QPushButton("Set Username", dialog)
        button.setDefault(True)
        button.clicked.connect(lambda: self.setUsername(usernameInput.text()))

        innerLayout = QHBoxLayout()
        innerLayout.addStretch()
        innerLayout.addWidget(usernameInput)
        innerLayout.addWidget(button)
        innerLayout.addStretch()

        dialogLayout = QVBoxLayout()
        dialogLayout.addStretch()
        dialogLayout.addLayout(innerLayout)
        dialogLayout.addStretch()

        dialog.setLayout(dialogLayout)

        return dialog

    # Sending Server the current Clients username
    def setUsername(self, username):
        self.client.setUsername(username)
        self.username = username

        header, sender, payload = self.client.getMesseges()
        if header != protocol.ACCEPT:
            print(header, sender, payload)
            return

        self.dialog.close()

        self.recieverThread = threading.Thread(target=self.recieveMessage, daemon=True)
        self.recieverThread.start()

    # Initial Dialog asking consent establish Connection
    def connectDialog(self):
        dialog = ModalDialog(self)
        dialog.setFixedSize(400, 200)

        button = QPushButton("Contect", dialog)
        button.setDefault(True)
        button.clicked.connect(self.connect)

        innerLayout = QHBoxLayout()
        innerLayout.addStretch()
        innerLayout.addWidget(button)
        innerLayout.addStretch()

        dialogLayout = QVBoxLayout()
        dialogLayout.addStretch()
        dialogLayout.addLayout(innerLayout)
        dialogLayout.addStretch()

        dialog.setLayout(dialogLayout)

        return dialog

    def SetupUI(self):
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        # Chat Text Display
        self.chatDisplay = QTextEdit(self.centralWidget)
        self.chatDisplay.setReadOnly(True)

        # Chat Input Text
        self.inputField = QLineEdit(self.centralWidget)

        # Send Message Button
        self.sendButton = QPushButton("Send", self.centralWidget)
        self.sendButton.setDefault(True)
        self.sendButton.clicked.connect(self.sendMessage)

        # Join Voice Button
        self.voiceButton = QPushButton("Voice", self.centralWidget)
        self.voiceButton.setCheckable(True)

        # Specifying Layout
        self.centralLayout = QGridLayout()
        self.centralLayout.addWidget(self.chatDisplay, 0, 0, 6, 7)
        self.centralLayout.addWidget(self.inputField, 6, 0, 1, 5)
        self.centralLayout.addWidget(self.sendButton, 6, 5, 1, 1)
        self.centralLayout.addWidget(self.voiceButton, 6, 6, 1, 1)

        self.centralWidget.setLayout(self.centralLayout)

    def presentChallenge(self, otherUser):
        self.dialog = ModalDialog(self)
        self.dialog.setFixedSize(400, 200)

        label = QLabel(self.dialog)
        label.setText("Challenge Recieved from " + otherUser)

        acceptButton = QPushButton("Accept", self.dialog)
        acceptButton.setDefault(True)
        acceptButton.clicked.connect(lambda: self.challengeAccepted(otherUser))

        rejectButton = QPushButton("Reject", self.dialog)
        rejectButton.clicked.connect(lambda: self.challengeRejected(otherUser))        

        innerLayout = QHBoxLayout()
        innerLayout.addStretch()
        innerLayout.addWidget(acceptButton)
        innerLayout.addWidget(rejectButton)
        innerLayout.addStretch()

        dialogLayout = QVBoxLayout()
        dialogLayout.addStretch()
        dialogLayout.addWidget(label)
        dialogLayout.addLayout(innerLayout)
        dialogLayout.addStretch()

        self.dialog.setLayout(dialogLayout)
        self.dialog.exec_()

    def challengeAccepted(self, otherUser):
        self.client.sendCommands(protocol.CHALLENGE_ACCEPTED, otherUser)
        self.dialog.close()

    def challengeRejected(self, otherUser):
        self.client.sendCommands(protocol.CHALLENGE_REJECTED, otherUser)
        self.dialog.close()

    def startGame(self):
        print("Game Starts Now")

    # Sending Commands and messages as per the user input
    def sendMessage(self):
        message = self.inputField.text()
        self.inputField.setText("")
        if message != "":
            if message[0] == "#":
                splitted = message.split(" ")
                command = splitted[0]
                arg = ""
                if len(splitted) >= 2:
                    arg = splitted[1]

                if command == "#help":
                    self.client.sendCommands(protocol.HELP)
                elif command == "#getrooms":
                    self.client.sendCommands(protocol.GETROOMLIST)
                elif command == "#joinroom":
                    self.client.sendCommands(protocol.JOINROOM, arg)
                elif command == "#createroom":
                    self.client.sendCommands(protocol.CREATEROOM, arg)
                elif command == "#exitroom":
                    self.client.sendCommands(protocol.LEAVEROOM)
                elif command == "#challenge":
                    self.client.sendCommands(protocol.CHALLENGE, arg)
                else:
                    self.printcolored("Unknown Command : " + command, "red")
            else:
                self.client.sendCommands(protocol.MESSAGE, message)

    # prints colored text into the chat's display box
    def printcolored(self, msg, color):
        self.chatDisplay.append("<font color=" + color + ">" + msg + "</font>")

    # Wrapper for recieving Incoming Messages
    def recieveMessage(self):
        while True:
            header, sender, payload = self.client.getMesseges()
            if header == protocol.EXIT:
                break

            elif header == protocol.MESSAGE:
                self.printcolored(sender + "> " + payload, "white")

            elif header == protocol.HELP:
                self.printcolored(sender + "> " + payload, "Blue")

            elif header == protocol.ROOMLIST:
                self.printcolored(sender + "> " + payload, "white")

            elif header == protocol.REJECT:
                self.printcolored("Error> " + payload, "red")

            elif header == protocol.ACCEPT:
                self.printcolored(sender + "> " + payload, "green")

            elif header == protocol.UPDATE:
                self.printcolored(payload, "blue")

            elif header == protocol.CHALLENGE_RECIEVED:
                self.presentChallenge(sender)

            elif header == protocol.CHALLENGE_ACCEPTED:
                self.printcolored("Challenge Accepted ", "green")
                self.startGame()

            elif header == protocol.CHALLENGE_REJECTED:
                self.printcolored("Challenge Rejected ", "red")

            else:
                print("Unknown header : ", header)

    # Closing socket when user tries to close the application
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Quit", "Are You Sure to Quit?", QMessageBox.No | QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            # Informing Server about closing socket
            self.client.sendCommands(protocol.EXIT)

            # waiting for recieverThread to notice
            self.recieverThread.join()

            print("Threads Joined")

            # Closing Socket
            self.client.close()

            # Closing the application
            event.accept()
        else:
            event.ignore()


def Read_Config(filepath):
    config = {}
    with open(filepath, "r") as file:
        for line in file:
            line = line.split("=")
            config[line[0].strip()] = line[1].strip()

    return config


class ModalDialog(QDialog):
    def __init__(self, parent=None):
        super(ModalDialog, self).__init__(parent)

        # Blocking Input to all other Dialogs when this Dialog open
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())
