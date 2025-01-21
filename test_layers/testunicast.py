import socket
import random
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../layers")))
from layers.identity_layer import *

class TestLayer:
    def __init__(self):
        local_ip=""
        self.port=-1
        self.sock=self.initialize_unicast_socket()


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
        
        return sock

    def unicast_listen(self):
        print(f"Listening for UDP messages on port {self.port}...")

        while True:
            data, addr = self.sock.recvfrom(1024)  # Buffer size 1024 bytes
            print(json.loads(data))


    def unicast_message(self, message,addr):
        self.sock.sendto(message.encode(), addr) 

    def init(self):
        unilistener_thread = threading.Thread(target=self.unicast_listen, daemon=False)
        unilistener_thread.start()


def testcase1():
    idet=IdentityLayer()
    idet.init()

def testcase2():
    test=TestLayer()
    test.init()
    election = {
        "identity_type": "ELECTION",
        "peer_uuid": "ayush",
        "peer_unicast_id":"192.168.0.101",
        "peer_unicast_port":19578,
        "payload":"ayush"
        }
    test.unicast_message(json.dumps(election),("192.168.0.101",10449))
testcase2()    