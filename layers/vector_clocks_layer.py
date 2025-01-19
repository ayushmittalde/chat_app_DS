class Node:
    def __init__(self, node_id, total_nodes):
        self.node_id = node_id
        self.vector_clock = [0] * total_nodes

    def send_message(self, receiver, message_text):
        self.vector_clock[self.node_id] += 1
        message = Message(self.node_id, message_text, list(self.vector_clock))
        receiver.update_vector_clock(message)

    def update_vector_clock(self, message):
        """
        Update the vector clock based on the received message.
        """
        self.vector_clock = [max(vc1, vc2) for vc1, vc2 in zip(self.vector_clock, message.vector_clock)]
        self.vector_clock[self.node_id] += 1
        print(f"Node {self.node_id} received message: {message.text}")
        print(f"Updated vector clock: {self.vector_clock}")

    def __str__(self):
        return f"Node {self.node_id} - Vector Clock: {self.vector_clock}"

class Message:
    def __init__(self, sender_id, text, vector_clock):
        self.sender_id = sender_id
        self.text = text
        self.vector_clock = vector_clock

class DistributedSystem:
    def __init__(self, num_nodes):
        self.nodes = [Node(i, num_nodes) for i in range(num_nodes)]

    def simulate(self):
        # Node 0 sends a message to Node 1
        self.nodes[0].send_message(self.nodes[1], "Hello from Node 0")

        # Node 1 sends a message to Node 2
        self.nodes[1].send_message(self.nodes[2], "Hello from Node 1")

        # Node 2 sends a message to Node 0
        self.nodes[2].send_message(self.nodes[0], "Hello from Node 2")

        # Print final vector clocks
        for node in self.nodes:
            print(node)

# Example simulation
system = DistributedSystem(3)
system.simulate()