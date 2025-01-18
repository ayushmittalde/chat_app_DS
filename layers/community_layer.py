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
        self.id="0"
        ### Variables for Bully algorithim 
        self.bully_message_queue = queue.Queue()
        self.bullystate = "IDLE"
        self.started_election = False
        self.bullyrunning=False
        self.leader_id="NULL"
    
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
                    
                    if (key==self.leader_id):
                        message = {
                            "community_type": "ELECTION",
                            "election_type": "LEADER_FAIL",
                            "peer_uuid": self.id
                        }
                        self.leader_id="NULL"
                        self.bully_message_queue(message)


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
            if self.leader_id==self.id:
                self.set_groupview(data["peer_uuid"],time.time())
                response=self.send_join_response()
                self.send_response(response)

        elif(data["community_type"]=="WANT_TO_JOIN_RESPONSE"):
            #abstract leader information
            self.received_leader_response = True
            self.leader_id=data["leader_uuid"]
            print(data["participants"])
            self.update_groupview(data["participants"])
            self.print_groupview()
            print(f"leader id {self.leader_id}")


        elif(data["community_type"]=="HEARTBEAT"):
            if (self.get_groupview(data["peer_uuid"])!=None):
                self.set_groupview(data["peer_uuid"],time.time())
            else :
                print(f"{data} ignored in heartbeat")

        elif(data["community_type"]=="ELECTION"):
            self.bully_message_queue.put(data)

    def send_join_response(self):
        participant=self.get_groupview_copy()
        response = {
            "community_type": "WANT_TO_JOIN_RESPONSE",
            "last_messages": self.message_history[-20:],
            "leader_uuid":self.leader_id,
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

    def state_machine(self):
        """
        The main state machine for the election process.
        Follows the state diagram flow:
        Detect leader failure → Trigger election.
        Send "ELECTION" to higher UUIDs → Wait for "RESPONSE" or timeout.
        If no response → Declare self as leader → Multicast "COORDINATOR".
        If "RESPONSE" received → Wait for "COORDINATOR" message.
        Dynamically process messages like "ELECTION", "RESPONSE", and "COORDINATOR" at any state.
        """
        while self.bullyrunning:

            if self.bullystate == "IDLE":
                self.wait_for_elecmsg() # handling messages in IDLE state
                print(f"Bully Algorithim next state {self.bullystate}")
                time.sleep(2)  # Prevent busy-waiting

            # 2. State handling for election process
            if self.bullystate == "ELECTION":
                # Send election messages to higher UUIDs
                self.start_election()
                # Next : Wait for responses or declare itself as leader
                print(f"Bully Algorithim next state {self.bullystate}")

            #3 can go to LEADER state , IDLE state and WAITING COD state
            if self.bullystate == "WAITING RESPONSE":
                # If we're waiting for a RESPONSE, handle the timeout or successful response
                self.wait_for_responses()
                print(f"Bully Algorithim next state {self.bullystate}")

            # if leader responds then this will change to IDLE or ELECTION state
            if self.bullystate == "WAITING COD":
                self.wait_for_coordinator()
                print(f"Bully Algorithim next state {self.bullystate}")
           
            # end the election
            if self.bullystate == "LEADER":
                self.send_coordinator_message()
                self.bullystate="IDLE"
                self.received_leader_heartbeat=True
                self.started_election = False
                print(f"Bully Algorithim next state {self.bullystate}")

            time.sleep(0.5)  # Prevent busy-waiting

    def start_election(self): # Final 
        """
        Start the election process by sending an ELECTION message to nodes with higher UUIDs.
        """
        if self.bullystate == "ELECTION":
            self.bullystate = "WAITING RESPONSE"
            self.broadcast_election()
            self.started_election = True

    def broadcast_election(self): #Final
        """
        Send the ELECTION message to other participants with higher UUIDs if election has not been started by this node
        """
        if self.started_election == False :
            higher_node=False
            message = {
            "community_type": "ELECTION",
            "election_type": "ELECTION",
            "peer_uuid": self.id
            }
            participant=self.get_groupview_copy()

            for key in list(participant.keys()):
                if (key> self.id):
                    self.broadcast_elecmsg(message,key)
                    # check if there are any higher node in the group view
                    higher_node=True    
            
            # declare itself as leader if there are no higher node
            if not higher_node:
                self.declare_self_as_leader()

    def wait_for_elecmsg(self):   #Final 
        got_message=False

        # Get the message from the Queue and process it, if queue is empty exception is raised
        try:
            message = self.bully_message_queue.get_nowait()
            got_message=True
        except queue.Empty:
            # This is done to make sure print is there for only one time
                print(f"No message in the bully algorithim queue")

        if got_message==True:
            got_message=False
            # Check if a RESPONSE message is received
            # This will change the state to "WAITING COD"
            if (self.received_response_message(message)==True):  
                # do not process , should not happen 
                pass
            
            # Check if an ELECTION message is received
            elif self.received_election_message(message):  
                # Respond to the election message
                id =message["peer_uuid"]
                self.send_response_message(id)
                self.bullystate="ELECTION"

            # Check if a COORDINATOR message is received
            # Stop election process and acknowledge the new leader
            # Change the state to IDLE
            #Election Ended
            elif self.received_coordinator_message(message):  
                id =message["peer_uuid"]
                self.acknowledge_coordinator_message(id)
                self.bullystate="IDLE" 

            #special case when we receive CO-OD from a lower id , we should start an election
            elif (message["peer_uuid"]<self.id and message["election_type"]=="COORDINATOR"):
                # Our id is bigger than ours so wrong election 
                self.bullystate="ELECTION"
            
            elif ((message["election_type"]=="ATTEMPT_JOIN_FAIL") or (message["election_type"]== "LEADER_FAIL")):
                self.bullystate="ELECTION"


    def wait_for_responses(self):   #Final 
        timeout = shared_data_instance.ACK_ELECTION_TIMEOUT
        start_time = time.time()
        got_message=False
        printcount=0

        while time.time() - start_time < timeout:
            # Get the message from the Queue and process it, if queue is empty exception is raised
            try:
                message = self.bully_message_queue.get_nowait()
                got_message=True
            except queue.Empty:
                # This is done to make sure print is there for only one time
                if printcount==0:
                    print(f"No message in the bully algorithim queue")
                    printcount=1

            if got_message==True:
                got_message=False
                # Check if a RESPONSE message is received
                # This will change the state to "WAITING COD"
                if (self.received_response_message(message)==True):  
                    self.bullystate="WAITING COD"
                    return

                # Check if an ELECTION message is received
                elif self.received_election_message(message):  
                    # Respond to the election message
                    id =message["peer_uuid"]
                    self.send_response_message(id)

                # Check if a COORDINATOR message is received
                # Stop election process and acknowledge the new leader
                # Change the state to IDLE
                #Election Ended
                elif self.received_coordinator_message(message):  
                    id =message["peer_uuid"]
                    self.acknowledge_coordinator_message(id)
                    return 
        print(f"Timeout awaiting response")
        # If no response received, declare self as leader and send COORDINATOR and change the state to LEADER
        self.declare_self_as_leader()

    def received_response_message(self,message):    #FINAL used in Wait response
        # Check if a RESPONSE message has been received, (message["peer_uuid"]>self.id) is a nautal condition
        if ((message["election_type"]=="RESPONSE") and (message["peer_uuid"]>self.id) ):
            print(f" Message processed as response {message}")
            return True
        else :
            print(f" Message ignored as response {message}")
            return False
        
    def received_election_message(self,message): #Final , correct 
        # Check if an ELECTION message has been received
        if (message["election_type"]=="ELECTION" and (message["peer_uuid"]<self.id) ):
            print(f"Message processed as election {message}")
            return True
        else :
            print(f"Message ignored as election {message}")
            return False
        
    def received_coordinator_message(self,message): #Final , correct
        if (message["election_type"]=="COORDINATOR" and (message["peer_uuid"]>self.id) ):
            print(f"Message processed as co-ordinator {message}")
            return True
        else :
            # we are not doing anything if we receive co-ordinator message from a lower node because we are already in the elction , will over run him in near future
            print(f"Message ignored as co-ordinator {message}")
            return False
    
    def send_response_message(self, peer_uuid): #Final , correct
        """
        Send a RESPONSE message back to the peer UUID.
        """
        if peer_uuid<self.id: # Usually this should hold implicitly but writing this condition to enforce Bully algo characterstics, this also enable us to shift algorithim to multicast
            message = {
                "community_type": "ELECTION",
                "election_type": "RESPONSE",
                "peer_uuid": self.id
            }
            self.broadcast_elecmsg(message, peer_uuid)
        else :
            print(f"Message ignored because uuid was higher {peer_uuid}")
    
    def acknowledge_coordinator_message(self,id):   #Final , correct
        """
        Acknowledge the COORDINATOR message and mark the leader election process as complete.
        """
        if id>self.id: # Usually this should hold implicitly but writing this condition to enforce Bully algo characterstics, this also enable us to shift algorithim to multicast
            self.leader_id=id
            print(f"Node {self.leader_id} is the leader.")
            self.received_leader_heartbeat=True
            self.bullystate = "IDLE"
        else :
            # if we see a smaller id coode then we should start an election if we are idle , if already in between election then start it
            print(f"Message ignored because uuid was smaller {id}")

    def declare_self_as_leader(self):   #Final 
        """
        Declare this node as the leader and send a COORDINATOR message to all participants.
        """
        self.leader_id=self.id
        self.bullystate = "LEADER"

    def send_coordinator_message(self): #Final
        """
        Send the COORDINATOR message to all participants.
        """
        message = {
            "community_type": "ELECTION",
            "election_type": "COORDINATOR",
            "peer_uuid": self.id
        }
        self.broadcast_elecmsg(message,"NULL")

    def wait_for_coordinator(self):   #Final 
        timeout = shared_data_instance.ELECTION_COD_TIMEOUT
        start_time = time.time()
        got_message=False
        printcount=0

        while time.time() - start_time < timeout:
            # Get the message from the Queue and process it, if queue is empty exception is raised
            try:
                message = self.bully_message_queue.get_nowait()
                got_message=True
            except queue.Empty:
                if printcount==0:
                    print(f"No message in the bully algorithim queue")
                    printcount=1
            
            if got_message==True:
                got_message=False
                # Check if a RESPONSE message is received
                # No state change
                if self.received_response_message(message):  
                    pass # One or more higher nodes is responding to my previous ELECTION message

                # Check if an ELECTION message is received
                # No state change 
                elif self.received_election_message(message):  
                    # Respond to the election message
                    id =message["peer_uuid"]
                    self.send_response_message(id)

                # Check if a COORDINATOR message is received
                # Stop election process and acknowledge the new leader
                # Change the state to IDLE
                #Election Ended
                elif self.received_coordinator_message(message):  
                    id =message["peer_uuid"]
                    self.acknowledge_coordinator_message(id)
                    return 

        print(f"Timeout awaiting co-od")
        self.started_election=False
        # If no response co-ordinator message is received, this means we have to restart the election 
        self.bullystate="ELECTION"


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
                    time.sleep(0.1)  # Small sleep to avoid busy waiting
                if joined:
                    break
            except Exception as e:
                print(f"Error attempting to join: {e}")
        if not joined:
            # sending message to bully algorithim to start the election
            message = {
                "community_type": "ELECTION",
                "election_type": "ATTEMPT_JOIN_FAIL",
                "peer_uuid": self.id
            }
            print("Failed to join after maximum retries. Starting election ")
            self.bully_message_queue.put(message)
        else:
            print("Node successfully joined the group!")

    def set_ordering_layer(self, ordering_layer):
        from .ordering_layer import OrderingLayer
        self.ordering_layer: OrderingLayer = ordering_layer

    def set_reliablity_layer(self, reliability_layer):
        from .reliability_layer import ReliabilityLayer
        self.reliablity_layer: ReliabilityLayer = reliability_layer

    def init(self):
        #starting Bully algorithim
        self.id=str(self.reliablity_layer.identity_layer.uuid)
        self.reliablity_layer.init()
        self.bullyrunning = True
        self.group_participants[self.id]=time.time()
        state_machine_thread = threading.Thread(target=self.state_machine, daemon=False)
        state_machine_thread.start()

        #can lead to election
        self.attempt_join()

        #starting heartbeat and group view once we have participants
        #self.start_heartbeat()

    def log_event(self, event_message: str):
        self.ordering_layer.log_event(event_message)
