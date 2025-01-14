from config import shared_data_instance
import uuid
import socket
import random


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
        self.port = random.randint(10000, 11000) #
        self.multicast_address = shared_data_instance.GROUP_ADDRESS
        self.multicast_port = shared_data_instance.GROUP_PORT
        self.sock = self.initialize_multicast_socket()
        print(f"Node initialized with UUID: {self.uuid} on port: {self.port}")


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
    
    def multicast_listen(self):
        print("Listening to multicast messages...") #
        self._log_event("Listening to multicast messages...")
        print(self.is_leader)
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                self.reliability_layer.handle_message(data.decode(), addr)
            except Exception as e:
                print(f"Error receiving multicast message: {e}")    #
                self._log_event(f"Error receiving multicast message: {e}")

    def broadcast_message(self, message):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                sock.bind(('', self.port))
                sock.sendto(message.encode(), (self.multicast_address, self.multicast_port))
                sock.close()
            except Exception as e:
                print(f"Error broadcasting message: {e}")
                self._log_event(f"Error broadcasting message: {e}")
    
    def set_reliability_layer(self, reliability_layer):
        from .reliability_layer import ReliabilityLayer
        self.reliability_layer: ReliabilityLayer = reliability_layer

    def init(self):
        pass
        
    def _log_event(self, event_message: str):
        #self.reliability_layer.log_event(event_message)
        pass
