import uuid
import socket
import threading
import random
import time

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
        self.sock = self.initialize_multicast_socket()
        print(f"Node initialized with UUID: {self.uuid} on port: {self.port}")

    def initialize_multicast_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.multicast_port))
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(self.multicast_address) + socket.inet_aton("0.0.0.0")
        )
        return sock

    def assign_free_port(self):
        return random.randint(10000, 11000)

    def multicast_listen(self):
        print("Listening to multicast messages...")
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                self.handle_message(data.decode(), addr)
            except Exception as e:
                print(f"Error receiving multicast message: {e}")

    def broadcast_message(self, message):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.bind(('', self.port))
            sock.sendto(message.encode(), (self.multicast_address, self.multicast_port))
            sock.close()
        except Exception as e:
            print(f"Error broadcasting message: {e}")

    def handle_message(self, message, addr):
        print(f"Received message: {message} from {addr}")
        if message.startswith("WANT_TO_JOIN"):
            if self.is_leader:
                self.send_join_response(addr)
        elif message.startswith("JOIN_RESPONSE"):
            self.received_leader_response = True
        elif message.startswith("HEARTBEAT"):
            self.received_leader_heartbeat = True

    def send_join_response(self, addr):
        try:
            response = {
                "last_messages": self.message_history[-20:],
                "participants": self.group_participants
            }
            print(f"Sending JOIN_RESPONSE to {addr}")
            self.broadcast_message(f"JOIN_RESPONSE {response}")
        except Exception as e:
            print(f"Error sending join response: {e}")

    def attempt_join(self):
        joined = False
        for attempt in range(self.max_retries):
            try:
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
            except Exception as e:
                print(f"Error attempting to join: {e}")
        if not joined:
            print("Failed to join after maximum retries.")
        else:
            print("Node successfully joined the group!")

    def simulate_heartbeat(self):
        if self.is_leader:
            while True:
                try:
                    print("Sending heartbeat...")
                    self.broadcast_message("HEARTBEAT")
                    time.sleep(5)
                except Exception as e:
                    print(f"Error simulating heartbeat: {e}")

def main():
    is_leader = input("Is this node the leader? (yes/no): ").strip().lower() == "yes"
    node = Node(is_leader)
    listener_thread = threading.Thread(target=node.multicast_listen, daemon=True)
    listener_thread.start()

    if is_leader:
        heartbeat_thread = threading.Thread(target=node.simulate_heartbeat, daemon=True)
        heartbeat_thread.start()
    else:
        node.attempt_join()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unhandled error in main: {e}")