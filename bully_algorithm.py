from dynamic_discovery_of_host import Node
import threading
import time
import uuid

class BullyAlgorithm(Node):
    def __init__(self, is_leader=False):
        super().__init__(is_leader)
        self.group_view = []  # The group view containing all active nodes

    def update_group_view(self, node_uuid, action="add"):
        if action == "add" and node_uuid not in self.group_view:
            self.group_view.append(node_uuid)
            print(f"Node {node_uuid} added to group view.")
        elif action == "remove" and node_uuid in self.group_view:
            self.group_view.remove(node_uuid)
            print(f"Node {node_uuid} removed from group view.")

    def handle_message(self, message, addr):
        super().handle_message(message, addr)
        if message.startswith("JOIN_REQUEST"):
            self.update_group_view(message.split()[1], action="add")
            if self.is_leader:
                self.send_join_response(addr)
        elif message.startswith("NODE_FAILURE"):
            self.update_group_view(message.split()[1], action="remove")
            if self.is_leader:
                print("Node failure detected.")
        elif message.startswith("ELECTION"):
            incoming_uuid = message.split()[1]
            if str(self.uuid) > incoming_uuid:
                print(f"Received ELECTION message from {incoming_uuid}. Responding with ANSWER.")
                self.broadcast_message(f"ANSWER {self.uuid}")
                self.start_election()
            else:
                print(f"Ignoring ELECTION message from {incoming_uuid}. My UUID is lower.")
        elif message.startswith("ANSWER"):
            print("Received ANSWER message. Higher-priority node exists.")
            self.received_leader_response = True
        elif message.startswith("COORDINATOR"):
            new_leader = message.split()[1]
            print(f"New leader elected: {new_leader}")
            self.is_leader = False
            self.received_leader_heartbeat = True
            self.update_group_view(new_leader, action="add")  # Ensure leader is in the group view

    def detect_leader_failure(self):
        if not self.received_leader_heartbeat:
            print("Leader failure detected. Starting election.")
            self.start_election()

    def start_election(self):
        print("Starting election...")
        self.received_leader_response = False  # Reset the response flag for each election
        self.broadcast_message(f"ELECTION {self.uuid}")
        self.wait_for_election_response()

    def wait_for_election_response(self):
        response_received = False
        for _ in range(20):  # Wait for up to 20 seconds
            time.sleep(1)
            if self.received_leader_response:
                response_received = True
                print("Received response from higher-priority node.")
                break
        if not response_received:
            print("No higher-priority response. Declaring self as leader.")
            self.is_leader = True
            self.received_leader_heartbeat = True  # Prevent further leader failure detection
            self.broadcast_message(f"COORDINATOR {self.uuid}")
            print(f"Node {self.uuid} is now the leader.")
            self.update_group_view(str(self.uuid), action="add")  # Ensure leader is in the group view

    def heartbeat_monitor(self):
        while True:
            time.sleep(10)  # Monitor every 10 seconds
            self.detect_leader_failure()

    def send_join_response(self, addr):
        try:
            response = {
                "last_messages": self.message_history[-20:],
                "participants": self.group_view
            }
            print(f"Sending JOIN_RESPONSE to {addr}")
            self.broadcast_message(f"JOIN_RESPONSE {response}")
        except Exception as e:
            print(f"Error sending join response: {e}")

    def confirm_leader_presence(self):
        while True:
            time.sleep(15)  # Check every 15 seconds
            if not self.is_leader and not self.received_leader_heartbeat:
                print("Leader confirmation timeout. Starting election.")
                self.start_election()

# Main function
if __name__ == "__main__":
    # Automatically decide if this node is the leader based on UUID or external criteria
    node_uuid = uuid.uuid4()
    is_leader = str(node_uuid).endswith("0")  # Example: decide leader based on UUID (arbitrary logic)
    print(f"Node UUID: {node_uuid}, Leader: {is_leader}")

    node = BullyAlgorithm(is_leader)

    listener_thread = threading.Thread(target=node.multicast_listen, daemon=True)
    listener_thread.start()

    if is_leader:
        heartbeat_thread = threading.Thread(target=node.simulate_heartbeat, daemon=True)
        heartbeat_thread.start()
    else:
        heartbeat_monitor_thread = threading.Thread(target=node.heartbeat_monitor, daemon=True)
        heartbeat_monitor_thread.start()
        leader_confirmation_thread = threading.Thread(target=node.confirm_leader_presence, daemon=True)
        leader_confirmation_thread.start()
        node.attempt_join()
