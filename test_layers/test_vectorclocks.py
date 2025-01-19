from layers.vector_clocks_layer import Node
from layers.vector_clocks_layer import DistributedSystem
from layers.vector_clocks_layer import Message
def test_update_vector_clock():
    node_a = Node(0, 3)
    node_b = Node(1, 3)

    # Simulate Node A sending a message to Node B
    node_a.vector_clock = [1, 0, 0]
    message = Message(0, "Message from A to B", list(node_a.vector_clock))

    node_b.update_vector_clock(message)

    # Node B should update its vector clock
    assert node_b.vector_clock == [1, 1, 0], f"Expected [1, 1, 0], but got {node_b.vector_clock}"
    print("Test Case 1 Passed!")

def test_distributed_system():
    system = DistributedSystem(3)

    # Simulate multiple messages
    system.nodes[0].send_message(system.nodes[1], "Message 1")
    system.nodes[1].send_message(system.nodes[2], "Message 2")
    system.nodes[2].send_message(system.nodes[0], "Message 3")

    # Expected final vector clocks
    assert system.nodes[0].vector_clock == [2, 2, 2], f"Node 0 vector clock incorrect: {system.nodes[0].vector_clock}"
    assert system.nodes[1].vector_clock == [1, 2, 0], f"Node 1 vector clock incorrect: {system.nodes[1].vector_clock}"
    assert system.nodes[2].vector_clock == [1, 2, 2], f"Node 2 vector clock incorrect: {system.nodes[2].vector_clock}"

    print("Test Case 2 Passed!")