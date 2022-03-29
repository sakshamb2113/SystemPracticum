# SystemPracticum
Mini Project for course CS-307

# Application Layer Protocol:
8 bytes Header
22 bytes Sender
4 bytes size of payload
payload

- SETUSRNM : Set User Name
- ACCEPT__ : Request Accepted
- REJECT__ : Request Rejected
- CREATERM : Create New Room Request
- GETROOMS : Get List of Rooms
- LISTROOM : List of Available Rooms Sent by the Server
- ROOMJOIN : Room Join Request
- EXITROOM : Exit to lobby
- CHLNG___ : Challenge another user to play
- CHLNGACC : Accept Challenge
- CHJNGREJ : Reject Challenge
- CHLNGRCV : Recieved Challenge from some user
- CONNGAME : Connect to Game Server
- ENDGAME_ : Disconnected from Game Server
- MESSAGE_ : Chat Message
- EXIT____ : Close Connection
- GAMEJOIN : Game Join Request
- GAMEUPDT : Game Info
- EXITGAME : Game Exit Request

# How to run
 - create a .config file with the required host and port
```
host=127.0.0.1
port=10000
```

 - create a virtual env `python -m venv .env`
 - activate the virtual env `source ./.env/bin/activate`
 - install the required libraries `pip install -r requirements.txt`
 - Run Server `python Server.py`
 - open one or multiple new terminals and activate virtual environment in them
 - Run Client in each of them `python ClientApp.py`
