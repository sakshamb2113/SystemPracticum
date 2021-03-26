from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
from Client import client
import threading

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.client = client()

        self.setWindowTitle("Gaminal")
        self.setFixedSize(600, 600)

        self.SetupUI()
        self.dialog = self.connectDialog()
        self.dialog.show()


    def connect(self):
        self.client.connect()

        self.dialog.close()
        self.dialog = self.usernameDialog()
        self.dialog.show()


    def usernameDialog(self):
        dialog = QDialog(self)
        dialog.setFixedSize(400,200)

        usernameInput = QLineEdit(dialog)
        usernameInput.setPlaceholderText("Username...")
        button = QPushButton("Set Username", dialog)
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
    
    def setUsername(self, username):
        self.client.setUsername(username)
        self.username = username

        self.dialog.close()

        self.recieverThread = threading.Thread(target=self.recieveMessage)
        self.recieverThread.start()

    def connectDialog(self):
        dialog = QDialog(self)
        dialog.setFixedSize(400,200)

        button = QPushButton("Contect", dialog)
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
    
    def sendMessage(self):
        message = self.inputField.text()
        if (message != ""):
            self.client.sendCommands(self.username + " : " + message)
    
    def recieveMessage(self):
        while (True):
            message = self.client.getMesseges()

            self.chatDisplay.append(message + "\n")


def Read_Config(filepath):
    config = {}
    with open(filepath, "r") as file:
        for line in file:
            line = line.split("=")
            config[line[0].strip()] = line[1].strip()
    
    return config


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())