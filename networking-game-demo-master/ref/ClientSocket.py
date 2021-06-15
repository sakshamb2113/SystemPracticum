import socket
import time

# faster implementation of a queue in python. Operates in O(1) time instead of a standard list O(n) time.
from collections import deque
import json

UDP_IP = "127.0.0.1"
UDP_PORT = 9652

SEND_DELAY = 200        # the offset aimed for in milliseconds
TEST_RUNTIME = 10       # how many seconds the test runs
POLL_RATE = 64         # the number of packets sent per second

client_conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_conn.bind(('', UDP_PORT))
client_conn.setblocking(1)          # used for frame locking to the network rate

print("Running packet delay analysis...\n")
packet_queue = deque()
packet_count = 0
average_ms = 0

while True:
    init_time = str(time.time_ns())

    # put the packet into a queue after they have waited in the queue long enough
    # this does cause some bandwidth overhead, just to note. For demonstration purposes, it's reasonable.
    packet = {
        "time": time.time_ns()
    }
    packet_queue.append(packet)

    # if the first list index is not empty:
    if len(packet_queue) > 0:
        # read the timestamp on it
        if time.time_ns()/1000000 - packet_queue[0].get("time")/1000000 >= SEND_DELAY:
            # if the timestamp >= latency, send the packet and move the list up.
            client_conn.sendto(str.encode(json.dumps(packet_queue.popleft())), (UDP_IP, 9653))

            # in the real application, we don't care about the loopback, so this is only for debugging.
            data, server = client_conn.recvfrom(1024)
            packet_count += 1
            send_time = int(json.loads(data.decode()).get("time"))
            diff = (time.time_ns() - send_time)/1000000

            average_ms = ((average_ms * (packet_count-1)) + diff)/packet_count

    if packet_count >= POLL_RATE * TEST_RUNTIME:
        client_conn.close()
        break

    time.sleep(1/POLL_RATE)

print(f"Runtime: {TEST_RUNTIME} seconds, polling {POLL_RATE} times per second")
print(f"Target delay:\t\t {SEND_DELAY}ms")
print(f"Evaluated delay:\t {round(average_ms, 2)}ms")
