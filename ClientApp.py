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
        dialog.setFixedSize(400,200)

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

        self.dialog.close()

        self.recieverThread = threading.Thread(target=self.recieveMessage, daemon=True)
        self.recieverThread.start()

    # Initial Dialog asking consent establish Connection
    def connectDialog(self):
        dialog = ModalDialog(self)
        dialog.setFixedSize(400,200)

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
    
    # Wrapper for Sending Commands
    def sendMessage(self):
        message = self.inputField.text()
        self.inputField.setText("")
        if (message != ""):
            self.client.sendCommands(self.username + " : " + message)
    
    # Wrapper for recieving Incoming Messages
    def recieveMessage(self):
        while (True):
            message = self.client.getMesseges()
            if(message == 'exit'):
                break

            self.chatDisplay.append(message)
    
    # Closing socket when user tries to close the application
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Quit', 'Are You Sure to Quit?', QMessageBox.No | QMessageBox.Yes)
        if (reply == QMessageBox.Yes):
            # Informing Server about closing socket
            self.client.sendCommands("exit")
            
            # waiting for recieverThread to notice 
            self.recieverThread.join()

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