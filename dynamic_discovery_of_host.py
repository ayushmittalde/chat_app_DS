import uuid
import socket
import threading
import random
import time
import os

class Node:
    def __init__(self, is_leader=False):
        self.uuid = uuid.uuid4()
        self.is_leader = is_leader
        self.port = self.assign_free_port()
        self.multicast_address = "224.0.0.10"
        self.multicast_port = 55000
        self.message_history = []  
        self.group_participants = []  
        self.retry_count = 0
        self.max_retries = 5
        self.received_leader_response = False
        self.received_leader_heartbeat = False
        print(f"Node initialized with UUID: {self.uuid} on port: {self.port}")

    def assign_free_port(self):
        # Assign a random port from a range
        return random.randint(10000, 11000)

    def multicast_listen(self):
        # Set up a socket to listen to multicast messages
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.multicast_port))

        # Add to multicast group
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(self.multicast_address) + socket.inet_aton("0.0.0.0")
        )

        print("Listening to multicast messages...")
        while True:
            data, addr = sock.recvfrom(1024)
            self.handle_message(data.decode(), addr)

    def broadcast_message(self, message):
        # Send a message to the multicast group
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.bind(('', self.port))
        sock.sendto(message.encode(), (self.multicast_address, self.multicast_port))

    def handle_message(self, message, addr):
        # Handle incoming messages
        print(f"Received message: {message} from {addr}")
        if message.startswith("WANT_TO_JOIN"):
            if self.is_leader:
                self.send_join_response(addr)
        elif message.startswith("JOIN_RESPONSE"):
            self.received_leader_response = True
        elif message.startswith("HEARTBEAT"):
            self.received_leader_heartbeat = True

    def send_join_response(self, addr):
        # Respond with the last 20 messages and participants
        response = {
            "last_messages": self.message_history[-20:],
            "participants": self.group_participants
        }
        print(f"Sending JOIN_RESPONSE to {addr}")
        self.broadcast_message(f"JOIN_RESPONSE {response}")

    def attempt_join(self):
        # Attempt to join the group
        joined = False
        for attempt in range(self.max_retries):
            delay = random.uniform(1, 5)
            print(f"Attempting to join (Attempt {attempt + 1}/{self.max_retries}). Waiting for {delay:.2f} seconds...")
            self.broadcast_message(f"WANT_TO_JOIN {self.uuid}")
            start_time = time.time()
            while time.time() - start_time < delay:
                if self.received_leader_response:
                    print("Successfully joined the group.")
                    joined = True
                    break
                if self.received_leader_heartbeat:
                    print("Heartbeat detected. Retrying join...")
                    break
                time.sleep(0.1)  # Small sleep to avoid busy waiting
            if joined:
                break
        if not joined:
            print("Failed to join after maximum retries.")
        else:
            print("Node successfully joined the group!")

    def simulate_heartbeat(self):
        # Leader sends periodic heartbeat
        if self.is_leader:
            while True:
                print("Sending heartbeat...")
                self.broadcast_message("HEARTBEAT")
                time.sleep(5)

def main():
    is_leader = input("Is this node the leader? (yes/no): ").strip().lower() == "yes"
    node = Node(is_leader)
    listener_thread = threading.Thread(target=node.multicast_listen)
    listener_thread.start()

    if is_leader:
        heartbeat_thread = threading.Thread(target=node.simulate_heartbeat)
        heartbeat_thread.start()
    else:
        node.attempt_join()

#main()