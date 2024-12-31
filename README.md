# Distributed System Chat Application
This repository contains the code for a Distributed System Project focused on implementing a decentralized chat application. The system ensures communication between nodes in a distributed environment, adhering to core principles like fault tolerance, scalability, and synchronization.

## Commit Guidelines
We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard to ensure clarity and consistency in commit messages. Please refer to the [Conventional Commits documentation](https://www.conventionalcommits.org/en/v1.0.0/) for detailed guidelines on how to format commit messages.

## Requirement Coverage
1. When a new user joins, they receive 20 new messages
	- Implementation: The leader responds to a “WANT_TO_JOIN” message with the last 20 messages stored in message_history.
	- Code Location: send_join_response method in the Node class.
2. When a new user joins, they send 20 new messages
	-	Implementation: This can be simulated by appending 20 dummy messages from the new user to the leader’s message_history.
	-	Enhancement Needed: Add functionality to simulate or broadcast 20 messages after joining.
3. A node will generate and assign itself a version 4 UUID
	-	Implementation: Each node generates a unique UUID during initialization using the uuid.uuid4() method.
	-	Code Location: __init__ method in the Node class.
4. A node will pick up a free port from the set of ports, different from the multicast port
	-	Implementation: A random port from a predefined range (10000-11000) is assigned to each node, ensuring it is different from the multicast port (55000).
	- Code Location: assign_free_port method in the Node class.
5. No two nodes on the same machine should pick the same port
	-	Implementation: Ports are randomly assigned to nodes, minimizing collisions. For stricter enforcement, a registry of used ports can be maintained.
	-	Code Location: assign_free_port method in the Node class.
6. Each node should listen on multicast address <224.0.0.10> and port <55000>
	-	Implementation: Nodes bind to the multicast address and port during initialization and listen for incoming messages.
	-	Code Location: multicast_listen method in the Node class.
7. A new node should broadcast a 'want to join' message to the leader
	-	Implementation: New nodes broadcast 'WANT_TO_JOIN {UUID}' messages to the multicast group.
	-	Code Location: attempt_join method in the Node class.
8. A leader should respond with 20 last messages and group participants
	-	Implementation: Upon receiving a 'WANT_TO_JOIN' message, the leader responds with the last 20 messages and the list of group participants.
	-	Code Location: send_join_response method in the Node class.
9. If no response is received for the 'want to join' message, then retry should occur 5 times
	-	Implementation: The joining node retries broadcasting 'WANT_TO_JOIN' up to max_retries (5).
	-	Code Location: attempt_join method in the Node class.
10. Each retry should occur at randomized duration, mitigating risk 1
	-	Implementation: Each retry waits for a random delay (between 1 and 5 seconds) before rebroadcasting.
	-	Code Location: attempt_join method in the Node class.
11. Each node should listen to the heartbeat of the leader while waiting for randomized duration, and if it receives the heartbeat, then requirement 7 should be executed again
	-	Implementation: Nodes listen for 'HEARTBEAT' messages from the leader. If received, the 'WANT_TO_JOIN' message is rebroadcast.
	-	Code Location: handle_message and attempt_join methods in the Node class.

## Things to improve for Bharat Puri 31.12.24
1. Initialiation of send and receive options at a central place (_inti_)
2. Only one class for Node in jupyter file and dynamic_discovery_of_host.py file.
