from config import shared_data_instance
import uuid
import socket
import random
import json
import os
import threading
import psutil

# For stress testing: Increase the chances of a send or receive failure!
TEST_FAILED_SEND_CHANCE = 0.0
TEST_FAILED_RECEIEVE_CHANCE = 0.0

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
        Return : Nothing
        """
        self.uuid = uuid.uuid4()
        self.is_leader = False
        self.port =-1       #unicast port
        self.local_ip=""    # unicast ip
        self.multicast_address = shared_data_instance.GROUP_ADDRESS
        self.multicast_port = shared_data_instance.GROUP_PORT           
        self.directory ={}                                              # maps uuids to ip address and port

    def get_wireless_interface(self):
        """
        Get the name of the wireless interface by checking available network interfaces.
        """
        wireless_keywords = ["wlan", "wi-fi", "wifi", "en0"]

        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    if any(keyword in interface.lower() for keyword in wireless_keywords):
                        return interface, addr.address
        raise Exception("No wireless interface found")
  
    def initialize_multicast_sendsocket(self):
        wireless_interface, wireless_ip = self.get_wireless_interface()
        self.log_event(f"Using wireless interface: {wireless_interface}, IP: {wireless_ip}")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        
        # Set the multicast interface before sending data
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(wireless_ip))

        # Set TTL to control packet forwarding scope
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        return sock

    def initialize_multicast_listsocket(self):
        """
        Type : Socket
        Purpose : Initialize the socket for multicast communication
        Args : Nothing
        Return : Socket Object
        
        """
        wireless_interface, wireless_ip = self.get_wireless_interface()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.multicast_port))
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(self.multicast_address) + socket.inet_aton(wireless_ip)
        )

        #sock.setsockopt(socket.IP_MULTICAST_IF,socket.inet_aton(wireless_ip))
        return sock

    def initialize_unicast_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        trying_bind=False 

        while not trying_bind:
            try:
                self.port=random.randint(10000, 11000) 
                sock.bind(('', self.port))
                trying_bind=True
            except:
                pass
        self.local_ip = socket.gethostbyname(socket.gethostname())
        self.log_event(f" Port {self.local_ip} IP : {self.port}")
        return sock

    def unicast_listen(self):
        self.log_event(f"Listening for UDP messages on port {self.port}...")

        while True:
            data, addr = self.uni_sock.recvfrom(2048)  # Buffer size 2048 bytes
            messages=data.decode().strip().split("\n")
            if 1 - random.random() > TEST_FAILED_RECEIEVE_CHANCE:
                for msg in messages:
                    try:
                        self.handle_message(msg)
                    except:
                        self.log_event("Identity Layer Error in splitting messages")

    def unicast_send(self, message,id):
        msg = {
        "peer_uuid": str(self.uuid),
        "peer_unicast_id":self.local_ip,
        "peer_unicast_port":self.port,
        "payload":message
        }
        jsonmsg=json.dumps(msg)
        jsonmsg=jsonmsg+"\n"
        addr=self.directory[id]
        if 1 - random.random() > TEST_FAILED_SEND_CHANCE:
            self.uni_sock.sendto(jsonmsg.encode(), addr)  
          
    def multicast_listen(self):
        self.log_event("Listening to multicast messages...") 

        while True:
            data, addr = self.multi_sock.recvfrom(2048)
            messages=data.decode().strip().split("\n")
            if 1 - random.random() > TEST_FAILED_RECEIEVE_CHANCE:
                for msg in messages:
                    try:
                        self.handle_message(msg)
                    except:
                        self.log_event("Identity Layer Error in splitting messages")

    def multicast_send(self, message):
        msg = {
                "peer_uuid": str(self.uuid),
                "peer_unicast_id":self.local_ip,
                "peer_unicast_port":self.port,
                "payload":message
                }
        jsonmsg=json.dumps(msg)
        jsonmsg=jsonmsg+"\n"
        if 1 - random.random() > TEST_FAILED_SEND_CHANCE:
            self.multi_sendsock.sendto(jsonmsg.encode(), (self.multicast_address, self.multicast_port))
    
    def handle_message(self,message: str):
        data=json.loads(message)
        self.directory[data["peer_uuid"]] = (data["peer_unicast_id"],int(data["peer_unicast_port"]))
        self.reliability_layer.handle_message(data["payload"])

    def set_reliability_layer(self, reliability_layer):
        from .reliability_layer import ReliabilityLayer
        self.reliability_layer: ReliabilityLayer = reliability_layer

    def init(self):
        self.uni_sock=self.initialize_unicast_socket()                  # initialize unicast channel
        self.multi_sock = self.initialize_multicast_listsocket()            # initialize multicast channel
        self.multi_sendsock=self.initialize_multicast_sendsocket()                  # initialize unicast channel
        self.log_event(f"Node initialized with UUID: {self.uuid} on port: {self.port} with pid : {os.getpid()}")

        multilistener_thread = threading.Thread(target=self.multicast_listen, daemon=True)
        unilistener_thread = threading.Thread(target=self.unicast_listen, daemon=True) 
        multilistener_thread.start()
        unilistener_thread.start()

    def log_event(self, event_message: str):
        self.reliability_layer.log_event(event_message)
        pass