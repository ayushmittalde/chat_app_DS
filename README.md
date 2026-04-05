<div align="center">
<img src="https://svg-banners.vercel.app/api?type=glitch&text1=Decentralized_Chat_APP&text2=Decentralized%20%E2%80%A2%20P2P%20%E2%80%A2%20Chat&width=1500&height=300" width="100%" alt="Agora — Decentralized P2P Chat" />
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Protocol-UDP_Multicast%2FUnicast-FF6B35?style=for-the-badge&logo=protocol&logoColor=white" />
  <img src="https://img.shields.io/badge/Algorithm-Bully_Election-6C63FF?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Ordering-Vector_Clocks-00B4D8?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-Academic-gray?style=for-the-badge" />
</p>
</div>

---

## What This Project Is

`Decentralized_Chat_APP` is a fully decentralised, peer-to-peer public chat room built in Python over a local-area network. All participants hold equal status — there is no dedicated server process. When a leader is required (for group-view management and new-node admittance), one is dynamically elected among the peers using the Bully Algorithm. The project demonstrates four core distributed-systems principles in combination: dynamic host discovery, fault-tolerant leader election, causal message ordering via vector clocks, and reliable communication over inherently lossy wireless UDP channels.

The system was developed as a group project for a Distributed Systems course. Team members: Ayush Mittal, Marawan Eldeib, Rico Haas, and Bharat Puri.

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
  - [Software Layers](#software-layers)
  - [Communication Channels](#communication-channels)
- [Distributed Systems Mechanisms](#distributed-systems-mechanisms)
  - [Dynamic Host Discovery](#dynamic-host-discovery)
  - [Leader Election — Bully Algorithm](#leader-election--bully-algorithm)
  - [Fault Tolerance](#fault-tolerance)
  - [Causal Message Ordering](#causal-message-ordering)
  - [Reliable Communication](#reliable-communication)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running a Node](#running-a-node)
  - [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Known Limitations](#known-limitations)
- [License](#license)

---

## Features

**Leaderless bootstrap :** any node can start the chat room; the first participant elects itself leader automatically after a 10-second timeout.

**Dynamic discovery :** a new node multicasts a WANT_TO_JOIN message and receives the complete group view, the current vector clock, and pending hold-back-queue messages from the leader, requiring no prior knowledge of any peer's address.

**Fault-tolerant leader election :** the Bully Algorithm elects the node with the highest UUID whenever the current leader stops sending heartbeats, including during concurrent node arrivals and mid-election crashes.

**Heartbeat monitoring :** every node multicasts a heartbeat at HEARTBEAT_INT (2 seconds); any participant missing a heartbeat for HEARTBEAT_TIMEOUT (5 seconds) is independently removed from each node's group view.

**Causal ordering :** vector clocks attached to every chat message ensure delivery respects causal dependencies across all nodes; out-of-order messages are held in a per-node hold-back queue until their dependencies are satisfied.

**Reliable unicast and multicast :** unacknowledged messages are retransmitted up to 15 times at 1.5-second intervals; multicast messages are sent a minimum of 8 times to compensate for unknown recipients on the wireless medium.

**Network-partition recovery :** when two previously disjoint groups merge onto the same LAN, UUID comparison forces the lower-UUID leader to step down and rejoin the surviving group.

**Terminal UI :** a terminal-based interface renders the chat room and handles user input without blocking the underlying communication layers.

---

## Architecture Overview

### Software Layers

The program employs a layered architecture modelled on the OSI stack. An outgoing chat message originates at the UI layer, travels downward through each layer — each encasing the message with layer-specific metadata — and exits through the network. An incoming packet follows the reverse path, each layer unpacking its encasing and taking the necessary action before passing the payload upward.

| Layer | Responsibility |
|---|---|
| **UI** | Renders the terminal interface; handles user input |
| **Application** | Composes outgoing messages; unpacks the final message content on receipt |
| **Ordering** | Attaches and validates vector clocks; manages the hold-back queue |
| **Community** | Runs the Bully Algorithm; maintains the group view; drives heartbeat monitoring |
| **Reliability** | Implements the ACK-based retransmission loop for unicast and multicast channels |
| **Identity** | Generates the node UUID (RFC 4122 v4); opens and maintains both UDP sockets |

### Communication Channels

Three distinct channel types carry different message classes:

| Channel | Reliability | Messages |
|---|---|---|
| Causal-ordered reliable multicast | Reliable + causally ordered | Chat messages |
| Reliable multicast | Reliable only | WANT_TO_JOIN_RESPONSE |
| Reliable UDP unicast | Reliable | ELECTION, RESPONSE |
| Unreliable UDP multicast | Best-effort | HEARTBEAT, WANT_TO_JOIN, TRY_JOIN_AGAIN |

---

## Distributed Systems Mechanisms

### Dynamic Host Discovery

When a new node starts, it generates a unique UUID and initializes both its unicast and multicast sockets. To discover the chat room's leader, it multicasts a WANT_TO_JOIN message to the shared multicast group. Only the current leader responds with a WANT_TO_JOIN_RESPONSE, which contains the leader UUID, the updated group view (including the joining node), the most recent vector clock state, and the recipient's UUID.

Should the WANT_TO_JOIN packet receive no response, the node retries a random number of times. If no leader is found after the maximum attempts, the node begins multicasting its own heartbeat. If an election is ongoing, the newly elected leader will detect the unknown heartbeat and issue a TRY_JOIN_AGAIN prompt, triggering a fresh WANT_TO_JOIN. If the node is the first participant, it initiates an election after 10 seconds to designate itself as leader.

**Consideration 1 (Sequence Number Reset):** Upon receiving WANT_TO_JOIN_RESPONSE, the new node resets its sequence number to 0. This prevents existing nodes from mistakenly placing the new node's first post-join message in the hold-back queue due to a non-zero sequence number carried over from any pre-join activity.

**Consideration 2 (Hold-Back Queue Replication):** Once the leader sends WANT_TO_JOIN_RESPONSE, it also multicasts the contents of its hold-back queue. The new node captures these messages and inserts them into its own hold-back queue, ensuring causal consistency from the moment it joins.

### Leader Election — Bully Algorithm

The Bully Algorithm was chosen as the leader election mechanism because the algorithm by design is capable of handling node failures. Our implementation follows a state-machine approach with four states: `Idle`, `Election`, `Waiting For Response`, and `Waiting For Coordinator`.

**UDP unicast** carries ELECTION messages to peers with higher UUIDs and RESPONSE messages to peers with lower UUIDs.

**UDP multicast** carries the COORDINATOR message to every participant.

The node with the highest UUID in the current group view is ultimately elected. Election initiation conditions include leader-heartbeat timeout, exhaustion of WANT_TO_JOIN retries by the first node, and receipt of a COORDINATOR message from a node with a lower UUID while in the Idle state.

### Fault Tolerance

The application is designed to detect and handle four failure classes:

**Node failure :** the failed participant is silently removed from each peer's group view based on heartbeat monitoring; no corrective action is required from the leader.

**Leader failure :** when the leader's heartbeat is absent for HEARTBEAT_TIMEOUT, all remaining nodes initiate an election simultaneously; the Bully Algorithm guarantees a single winner.

**Node failure during election :** if a node fails after sending a RESPONSE but before the COORDINATOR arrives, waiting nodes reach ELECTION_COD_TIMEOUT (5 seconds) and restart the election accordingly.

**Network partition :** when a partitioned group rejoins the LAN, the leader detects unknown heartbeats and multicasts a TRY_JOIN_AGAIN message. If the receiving node is itself a leader, it compares UUIDs: the lower-UUID leader steps down and rejoins, while the higher-UUID leader absorbs the new participant.

While this partition-recovery mechanism eventually converges to a single consistent group view, short-term inconsistencies may occur, particularly when two large groups merge simultaneously.

### Causal Message Ordering

Each chat message carries the sender's full vector clock as metadata. Before delivering any message to the application layer, a node evaluates two conditions:

**FIFO condition** — `receiver_vect_clock[S] + 1 == sender_vect_clock[S]`, ensuring no message from sender `S` is skipped.

**Causal dependency condition** — for every node `i` other than the sender, `sender_vect_clock[i] <= receiver_vect_clock[i]`, ensuring no causally prior messages are missing.

When either condition fails, the message is placed in the hold-back queue. After each delivery, the hold-back queue is re-evaluated to release any messages whose dependencies are now satisfied. To avoid race conditions introduced by dynamic group-view changes, vector-clock entries are never deleted when a node leaves — only added when a node joins.

Additionally, chat messages from the ordering layer are buffered in the community layer during an active election. Messages are only multicast once the election completes, ensuring proper vector-clock initialization for the newly elected leader.

### Reliable Communication

Reliable delivery is implemented at the reliability layer using a straightforward acknowledgement scheme. Each message is assigned a unique ID; the recipient acknowledges every received packet — including duplicates — while delivering each ID-and-sender-UUID combination only once.

– Unacknowledged unicast messages are retransmitted up to **15 times**, waiting **1.5 seconds** between attempts.
– Multicast messages are sent a minimum of **8 times**, since the full recipient list may not be known at send time.

This mechanism ensures that higher-level routines such as the Bully Algorithm can assume reliable communication channels.

---

## Getting Started

### Prerequisites

- Python 3.8 or later
- A local Wi-Fi network shared by all participating machines (all nodes must be on the same LAN and multicast group)
- No external Python packages are required beyond the standard library (`socket`, `uuid`, `threading`, `time`)

### Installation

```bash
# Clone the repository
git clone https://github.com/ayushmittalde/chat_app_DS.git
cd chat_app_DS
```

No additional installation steps are required. The application relies entirely on Python's standard library.

### Running a Node

Each participant runs one instance of the application. To start a node:

```bash
python main.py
```

When a node starts, it:
1. Generates a unique version-4 UUID (RFC 4122, Section 4.4).
2. Initializes a UDP unicast socket on a free port selected from a predefined range.
3. Initializes a UDP multicast socket bound to the shared multicast address and port.
4. Multicasts a WANT_TO_JOIN message to discover the current leader.

If no leader responds within the retry window, the node starts its own heartbeat and — if it is the first participant — elects itself leader after 10 seconds. Multiple nodes may be started simultaneously; the system accommodates concurrent initialization without significant degradation in user experience.

### Configuration

Network parameters are centralised in `layers/config.py`:

| Parameter | Default | Description |
|---|---|---|
| `MULTICAST_ADDRESS` | `224.0.0.10` | Shared multicast group address |
| `MULTICAST_PORT` | `55000` | Shared multicast group port |
| `HEARTBEAT_INT` | `2` seconds | Interval between each node's heartbeat multicast |
| `HEARTBEAT_TIMEOUT` | `5` seconds | Inactivity threshold before a participant is removed from group view |
| `ELECTION_COD_TIMEOUT` | `5` seconds | Timeout while waiting for a COORDINATOR message before restarting election |

---

## Project Structure

```
chat_app_DS/
├── main.py                        # Entry point — instantiates and wires all layers
├── layers/
│   ├── config.py                  # Network constants and timing parameters
│   ├── identity_layer.py          # UUID generation; UDP unicast and multicast sockets
│   ├── reliability_layer.py       # ACK-based retransmission for unicast and multicast
│   ├── community_layer.py         # Bully Algorithm; group view; heartbeat monitoring
│   ├── ordering_layer.py          # Vector clocks; hold-back queue; causal delivery
│   └── application_layer.py       # High-level message composition and unpacking
├── ui/
│   └── ui.py                      # Terminal UI rendering and user-input handling
├── test_bully/                    # Unit and integration tests for the Bully Algorithm
├── test_layers/                   # Tests for individual layer behaviour
├── Project_initialization.ipynb   # Jupyter notebook for project setup and exploration
└── README.md
```

---

## Known Limitations

**Vector clock growth** — entries are never deleted from the vector clock when a node leaves. When participant churn is frequent, this causes vector clocks and chat message payloads to grow unboundedly. Future work may consider a garbage-collection mechanism for obsolete clock entries.

**Network partition inconsistency** — when two groups merge after a partition, the group view may be temporarily inconsistent across participants. In some cases, the Bully Algorithm may elect a leader whose UUID is not the highest among all actual participants, because the group view is incomplete at the time of election. The system eventually converges, but the convergence window can be significant when large partitions merge.

**Asynchronous group view** — each node updates its local view of the network independently and asynchronously, leading to short-term divergence in how different nodes perceive group membership. Additionally, since every node monitors the heartbeat of every other participant, monitoring overhead scales linearly with group size, which may become a bottleneck in large deployments.

---

## License

No explicit open-source licence is applied to this repository. The project was developed for academic purposes as part of a Distributed Systems course. If you fork or adapt this work, ensure compliance with the licences of all transitive dependencies.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a1a2e,100:16213e&height=120&section=footer" width="100%" />

*Ayush Mittal · Marawan Eldeib · Rico Haas · Bharat Puri — Distributed Systems Project*

</div>
