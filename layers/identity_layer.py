from config import shared_data_instance
import uuid
import socket
import random
import json
import os
import threading
import psutil
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
        wireless_keywords = ["wlan", "wi-fi", "wifi"]

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
            data, addr = self.uni_sock.recvfrom(2048)  # Buffer size 1024 bytes
            messages=data.decode().strip().split("\n")
            for msg in messages:
                try:
                    self.handle_message(msg)
                except:
                    self.log_event("Identity Layer Error in splitting messages")

    def unicast_message(self, message,addr):
        message=message+"\n"
        self.uni_sock.sendto(message.encode(), addr)  
          
    def multicast_listen(self):
        self.log_event("Listening to multicast messages...") 

        while True:
            data, addr = self.multi_sock.recvfrom(2048)
            messages=data.decode().strip().split("\n")
            for msg in messages:
                try:
                    self.handle_message(msg)
                except:
                    self.log_event("Identity Layer Error in splitting messages")

            

    def broadcast_message(self, message):
        message=message+"\n"
        self.multi_sendsock.sendto(message.encode(), (self.multicast_address, self.multicast_port))

    def send_message(self,message: str):
        msg = {
                "identity_type": "MESSAGE",
                "peer_uuid": str(self.uuid),
                "peer_unicast_id":self.local_ip,
                "peer_unicast_port":self.port,
                "payload":message
                }
        self.broadcast_message(json.dumps(msg))

    def broadcast_heartbeat(self,message):
        beat = {
                "identity_type": "HEARTBEAT",
                "peer_uuid": str(self.uuid),
                "peer_unicast_id":self.local_ip,
                "peer_unicast_port":self.port,
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
        "peer_unicast_id":self.local_ip,
        "peer_unicast_port":self.port,
        "payload":message
        }
        if (id == "NULL"): # broadcast to everone (co-ordinator message)
            self.broadcast_message(json.dumps(election))
        else :
            addr=self.directory[id]
            self.unicast_message(json.dumps(election),addr)

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