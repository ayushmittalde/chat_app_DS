import json
import os
print(os.getcwd())
from layers.config import shared_data_instance
import random
import time
"""
To do: 
make use of the address in handle message

"""
class CommunityLayer:
    def __init__(self):
        self.message_history = ["Test1", "Test2","Test3"]  
        self.group_participants = []  
        self.retry_count = 0 #
        self.max_retries = 5 
        self.received_leader_response = False #
        self.received_leader_heartbeat = False #

    def handle_message(self, message, addr):
        """
        Type : Message Handling
        Purpose : Handles community layer messages
        Args : message not decoded to community layer json
        Return : Nothing
        """

        data=json.loads(message)                    # decodes json for the community layer
        print(data)
        if (data["community_type"]=="WANT_TO_JOIN"):
            if self.reliablity_layer.identity_layer.is_leader:
                print("Ayush",self.reliablity_layer.identity_layer.is_leader)
                response=self.send_join_response(addr)
                self.send_response(response)

        elif(data["community_type"]=="WANT_TO_JOIN_RESPONSE"):
            self.received_leader_response = True
            print ("Receiver ")
            print(data)
            print("\n")

        elif(data["community_type"]=="HEART_BEAT"):
            self.received_leader_heartbeat = True

    def send_join_response(self, addr):
        response = {
            "community_type": "WANT_TO_JOIN_RESPONSE",
            "last_messages": self.message_history[-20:],
            "participants": self.group_participants
        }
        return response

    def send_response(self,response):
        """
        Type : Message Handling
        Purpose : Send response to Identity layer
        Args : python dictionary
        Return : Nothing
        
        """
        self.reliablity_layer.send_response(json.dumps(response))

    def attempt_join(self):
        joined = False
        for attempt in range(self.max_retries):
            try:
                delay = random.uniform(1, 5)

                print(f"Attempting to join (Attempt {attempt + 1}/{self.max_retries}). Waiting for {delay:.2f} seconds...")
                message={
                    "community_type": "WANT_TO_JOIN",
                    "peer_uuid": str(self.reliablity_layer.identity_layer.uuid)
                }

                self.send_response(message)

                start_time = time.time()
                while time.time() - start_time < delay:
                    if self.received_leader_response:
                        print("Successfully joined the group.")
                        joined = True
                        break
                    if self.received_leader_heartbeat:
                        print("Heartbeat detected. Retrying join...")
                        break
                    time.sleep(0.1)  # Small sleep to avoid busy waiting
                if joined:
                    break
            except Exception as e:
                print(f"Error attempting to join: {e}")
        if not joined:
            print("Failed to join after maximum retries.")
        else:
            print("Node successfully joined the group!")

    def set_ordering_layer(self, ordering_layer):
        from .ordering_layer import OrderingLayer
        self.ordering_layer: OrderingLayer = ordering_layer

    def set_reliablity_layer(self, reliability_layer):
        from .reliability_layer import ReliabilityLayer
        self.reliablity_layer: ReliabilityLayer = reliability_layer

    def init(self):
        self.reliablity_layer.init()

    def log_event(self, event_message: str):
        self.ordering_layer.log_event(event_message)
