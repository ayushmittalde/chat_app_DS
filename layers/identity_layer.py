from config import shared_data_instance
import uuid
import socket
import random
import json
import os

"""
To do : 
1. Implement meant for which can discard some straight forward messages like for 
leader or not
2. No encoding into json right now in identity layer
"""
class IdentityLayer:

    def __init__(self):
        """
        Type : Constructor
        Purpose : Initialize the Identity layer
        Args : is_leader
        Return : Nothing
        """
        self.uuid = uuid.uuid4()
        self.is_leader = False
        self.port = random.randint(10000, 11000) 
        self.multicast_address = shared_data_instance.GROUP_ADDRESS
        self.multicast_port = shared_data_instance.GROUP_PORT           
        self.multi_sock = self.initialize_multicast_socket()            # initialize multicast channel
        self.uni_sock=self.initialize_unicast_socket()                  # initialize unicast channel
        self.directory ={}                                              # maps uuids to ip address and port
        print(f"Node initialized with UUID: {self.uuid} on port: {self.port} with pid : {os.getpid()}")

    def initialize_unicast_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.port))
        return sock

    def initialize_multicast_socket(self):
        """
        Type : Socket
        Purpose : Initialize the socket for multicast communication
        Args : Nothing
        Return : Socket Object
        
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.multicast_port))
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(self.multicast_address) + socket.inet_aton("0.0.0.0")
        )
        return sock

    def unicast_listen(self):
        print(f"Listening for UDP messages on port {self.port}...")

        while True:
            data, addr = self.uni_sock.recvfrom(1024)  # Buffer size 1024 bytes
            self.handle_message(data.decode(), addr)

    def unicast_message(self, message,addr):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.port))
        self.uni_sock.sendto(message.encode(), addr)
        sock.close()        
          
    def multicast_listen(self):
        print("Listening to multicast messages...") 

        while True:
            data, addr = self.multi_sock.recvfrom(1024)
            self.handle_message(data.decode(), addr)

    def broadcast_message(self, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.bind(('', self.port))
        sock.sendto(message.encode(), (self.multicast_address, self.multicast_port))
        sock.close()

    def send_message(self,message):
        msg = {
                "identity_type": "MESSAGE",
                "peer_uuid": str(self.uuid),
                "payload":message
                }
        self.broadcast_message(json.dumps(msg))

    def broadcast_heartbeat(self,message):
        beat = {
                "identity_type": "HEARTBEAT",
                "peer_uuid": str(self.uuid),
                "payload":message
                }
        self.broadcast_message(json.dumps(beat))
    
    def broadcast_elecmsg(self,message,id):
        """
        Type : Network
        Purpose : Sends election messages either on unicast channel to a specific address or broadcast to everyone (co-ordinator) message
        Args : message to be sent , id = uuid or NULL(broadcast to all)
        Return : Nothing
        """
        election = {
        "identity_type": "ELECTION",
        "peer_uuid": str(self.uuid),
        "payload":message
        }
        if (id == "NULL"): # broadcast to everone (co-ordinator message)
            self.broadcast_message(json.dumps(election))
        else :
            addr=self.directory[id]
            self.unicast_message(json.dumps(election),addr)

    def handle_message(self,message, addr):
        data=json.loads(message)
        self.directory[data["peer_uuid"]] = addr
        self.reliability_layer.handle_message(data["payload"])

    
    def set_reliability_layer(self, reliability_layer):
        from .reliability_layer import ReliabilityLayer
        self.reliability_layer: ReliabilityLayer = reliability_layer

    def init(self):
        pass
        
    def _log_event(self, event_message: str):
        #self.reliability_layer.log_event(event_message)
        pass
