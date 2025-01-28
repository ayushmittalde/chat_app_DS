# Distributed System Chat Application
This repository contains the code for a Distributed System Project focused on implementing a decentralized chat application. The system ensures communication between nodes in a distributed environment, adhering to core principles like causal ordering using vector clocks, bully algorithim , fault detection and tolerance along with reliable multicast.

## Requirement Coverage
1. When a new user joins, it replicates the state of the leader by copying the vector clock and messages from the hold back queue of the leader.
	- Implementation: The leader responds to a “WANT_TO_JOIN” message with its vector clock and multicasts the messages of its hold back queue.
	- Code Location: layers/community_layer
2. A node will generate and assign itself a version 4 UUID
	-	Implementation: Each node generates a unique UUID during initialization using the uuid.uuid4() method.
	-	Code Location: layers/identity_layer
3. A node will bind itself to two ports one for receiving and sending messages on the unicast channel and one for multicast channel.
	-	Implementation: layers/identity_layer
4. Each node should listen on multicast address <224.0.0.10> and port <55000>, this is configurable via layers/config.py
	-	Implementation: Nodes bind to the multicast address and port during initialization and listen for incoming messages.
	-	Code Location: layers/config.py
5. A new node should broadcast a 'WANT_TO_JOIN' message on the multicast group which is processed only by the leader. (Dynamic discovery of host)
	-	Implementation: New nodes broadcast 'WANT_TO_JOIN {UUID}' messages to the multicast group.
	-	Code Location: layers/community_layer
6. If no response is received for the 'WANT_TO_JOIN' message, then retry occurs for random number of times and the the node starts an election, since node has no group view, eventually it selects itself as the leader.
	-	Code Location: layers/community_layer.
7. Each node attemts for randomized number of times, which mitigates the risk that multiple nodes assume leader position at the same time.
	-	Code Location: layers/community_layer
8. Each node should listens to the heartbeat of every other node, and remove a participant from its group view if it receives no heartbeat for the specified timeout.
	-	Implementation: Nodes listen for 'HEARTBEAT' messages from every other node. When ever a node is accepted to the group with the "WANT_TO_JOIN_RESPONSE" message , every node updates their group view and add the new participant to it.
	-	Code Location: layers/community_layer

