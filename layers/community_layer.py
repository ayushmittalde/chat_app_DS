import json
import os
import threading
from layers.config import shared_data_instance
import random
import time
import queue
"""
To do: 
make use of the address in handle message

"""
class CommunityLayer:
    def __init__(self):
        self.retry_count = 0 
        self.max_retries = 5 
        self.received_leader_response = False 
        self.received_leader_heartbeat = False 
        self.running = False # used for heartbeat
        self.message_history = ["Test1", "Test2","Test3"]  
        self.lock = threading.Lock()
        self.group_participants = {}  
        self.id=str(self.reliablity_layer.identity_layer.uuid)
        ### Variables for Bully algorithim 
        self.bully_message_queue = queue.Queue()
        self.bullystate = "IDLE"
        self.started_election=False
    
    #### Helper Fucntion for group view ####

    def update_groupview(self, participants):
        with self.lock:
            self.group_participants=participants.copy()

    def get_groupview(self, key):
        with self.lock:
            return self.group_participants.get(key)
        
    def get_groupview_copy(self):
        with self.lock:
            return self.group_participants.copy()

    def set_groupview(self, key, value):
        with self.lock:
            self.group_participants[key] = value

    def remove_groupview(self, key):
        with self.lock:
            if key in self.group_participants:
                del self.group_participants[key]

    def print_groupview(self):
        with self.lock:
            for key in self.group_participants:
                print(key)

    def group_view(self):
            while self.running:
                now = time.time()

                participant=self.get_groupview_copy()
                
                for key in list(participant.keys()):
                    if(now-participant[key]>=shared_data_instance.HEARTBEAT_TIMEOUT):
                        del participant[key]

                self.update_groupview(participant)
                del participant
                self.print_groupview()
                time.sleep(shared_data_instance.HEARTBEAT_TIMEOUT)
    
    #### Helper Fucntion for group view ####
    #### Message Handling ####

    def handle_message(self, message):
        """
        Type : Message Handling
        Purpose : Handles community layer messages
        Args : message not decoded to community layer json
        Return : Nothing
        """
        data=json.loads(message)                    # decodes json for the community layer

        if (data["community_type"]=="WANT_TO_JOIN"):
            if self.reliablity_layer.identity_layer.is_leader:
                response=self.send_join_response()
                self.send_response(response)
                self.set_groupview(data["peer_uuid"],time.time())

        elif(data["community_type"]=="WANT_TO_JOIN_RESPONSE"):
            self.received_leader_response = True

        elif(data["community_type"]=="HEARTBEAT"):
            self.set_groupview(data["peer_uuid"],time.time())

        elif(data["community_type"]=="ELECTION"):
            self.bully_message_queue.put(data)


    def send_join_response(self):
        participant=self.get_groupview_copy()
        response = {
            "community_type": "WANT_TO_JOIN_RESPONSE",
            "last_messages": self.message_history[-20:],
            "participants": participant
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

    def broadcast_elecmsg(self,message,key):
        """
        Type : Message Handling
        Purpose : Send response to Identity layer
        Args : python dictionary
        Return : Nothing
        """
        self.reliablity_layer.broadcast_elecmsg(json.dumps(message),key)  

    #### Message Handling ####
    #### Heart Beat ####

    def start_heartbeat(self):
        self.running = True
        thread = threading.Thread(target=self.heartbeat, daemon=True)
        thread.start()

        thread_groupview = threading.Thread(target=self.group_view, daemon=True)
        thread_groupview.start()

    def heartbeat(self):
        while self.running:
            beat = {
            "community_type": "HEARTBEAT",
            "peer_uuid": self.id
            }
            self.reliablity_layer.send_heartbeat(json.dumps(beat))
            time.sleep(shared_data_instance.HEARTBEAT_INT) 
    
    def stop_heartbeat(self):
        self.running = False
        
    #### Heart Beat ####

    #### Bully Algorithim ###
    #### Bully Algorithim ####

    def attempt_join(self):
        joined = False
        for attempt in range(self.max_retries):
            try:
                delay = random.uniform(1, 5)

                print(f"Attempting to join (Attempt {attempt + 1}/{self.max_retries}). Waiting for {delay:.2f} seconds...")
                message={
                    "community_type": "WANT_TO_JOIN",
                    "peer_uuid": self.id
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
