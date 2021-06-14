import socket

# test variables
MESSAGE = "Hello World!"
UDP_PORT = 9653
UDP_IP = "127.0.0.1"  # the local adapter to bind to send out packets

# establish socket object. SOCK_DGRAM indicates a UDP data frame, stored in a static context.
conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
conn.bind(('', UDP_PORT))

# wait for connections on the port. If some are found, send data to them.
# This must be sent as a bytestream, objects don't work here.

# TODO make this with a configurable delay period
print(f"Deploying Server on {UDP_IP}:{UDP_PORT}")

# echo all requests
while True:
    d = conn.recvfrom(1024)
    data = d[0]
    addr = d[1]
    print(f"connection from: {addr}")
    conn.sendto(data, ('127.0.0.1', 9652))
