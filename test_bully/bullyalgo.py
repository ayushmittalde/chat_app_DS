import threading
import time
import json
import queue
from config import shared_data_instance
import sys
class CommunityLayer:
    def __init__(self):
        self.retry_count = 0
        self.max_retries = 5
        self.received_leader_response = False
        self.received_leader_heartbeat = True
        self.running = False  # used for heartbeat
        self.message_history = ["Test1", "Test2", "Test3"]
        self.lock = threading.Lock()
        self.group_participants = {"1":0,
                                   "2":0,
                                   "3":0,
                                   "4":0,
                                   "5":0
                                    }
        self.id = "5"
        
        # Bully algo variables
        self.bully_message_queue = queue.Queue()
        self.bullystate = "IDLE"
        self.started_election = False
        self.bullyrunning=False
        self.leader_id="NULL"

    def broadcast_elecmsg(self,message,key):
        if key =="NULL":
            print(f"Message sent to uuid everyone \n Message : {message} " )
        else :
            print(f"Message sent to uuid {key} \n Message : {message} " )

    def get_groupview_copy(self):
        return self.group_participants.copy()

    def start(self):
        """
        Start the thread to follow the state diagram and process leader failure, election, and coordination.
        """
        # Start the main state loop
        self.bullyrunning = True
        self.state_machine_thread = threading.Thread(target=self.state_machine, daemon=False)
        self.state_machine_thread.start()
    def stop(self):
        self.bullyrunning = False

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
                if (self.received_leader_heartbeat==True):
                    time.sleep(2)  # Prevent busy-waiting
                else:
                    self.bullystate = "ELECTION"

                print(f"Bully Algorithim next state {self.bullystate}")

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
                print(f"Bully Algorithim next state {self.bullystate}")

            time.sleep(0.5)  # Prevent busy-waiting

    def start_election(self): # Final 
        """
        Start the election process by sending an ELECTION message to nodes with higher UUIDs.
        """
        if self.bullystate == "ELECTION":
            self.bullystate = "WAITING RESPONSE"
            self.started_election = True
            self.broadcast_election()

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

    def wait_for_responses(self):   #Final 
        timeout = shared_data_instance.ACK_ELECTION_TIMEOUT
        start_time = time.time()
        got_message=False


        while time.time() - start_time < timeout:
            # Get the message from the Queue and process it, if queue is empty exception is raised
            try:
                message = self.bully_message_queue.get_nowait()
                got_message=True
            except queue.Empty:
                print(f"No message in the bully algorithim queue")

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
                    self.acknowledge_coordinator_message()
                    return 

        # If no response received, declare self as leader and send COORDINATOR and change the state to LEADER
        self.declare_self_as_leader()

    def received_response_message(self,message):    #FINAL used in Wait response
        # Check if a RESPONSE message has been received, (message["peer_uuid"]>self.id) is a nautal condition
        if ((message["election_type"]=="RESPONSE") and (message["peer_uuid"]>self.id) ):
            return True
        else :
            return False
        
    def received_election_message(self,message): #Final , correct 
        # Check if an ELECTION message has been received
        if (message["election_type"]=="ELECTION" and (message["peer_uuid"]<self.id) ):
            return True
        else :
            return False
        
    def received_coordinator_message(self,message): #Final , correct
        if (message["election_type"]=="COORDINATOR" and (message["peer_uuid"]>self.id) ):
            return True
        else :
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
    
    def acknowledge_coordinator_message(self,id):   #Final , correct
        """
        Acknowledge the COORDINATOR message and mark the leader election process as complete.
        """
        if id>self.id: # Usually this should hold implicitly but writing this condition to enforce Bully algo characterstics, this also enable us to shift algorithim to multicast
            self.leader_id=id
            print(f"Node {self.leader_id} is the leader.")
            self.received_leader_heartbeat=True
            self.bullystate = "IDLE"

    def declare_self_as_leader(self):   #Final 
        """
        Declare this node as the leader and send a COORDINATOR message to all participants.
        """
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

        while time.time() - start_time < timeout:
            # Get the message from the Queue and process it, if queue is empty exception is raised
            try:
                message = self.bully_message_queue.get_nowait()
                got_message=True
            except queue.Empty:
                print(f"No message in the bully algorithim queue")
            
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

        # If no response co-ordinator message is received, this means we have to restart the election 
        self.bullystate="ELECTION"

    def acknowledge_coordinator(self,id):   #Final , correct
        """
        Acknowledge the COORDINATOR message and mark the leader election process as complete.
        """
        self.leader_id=id
        print(f"Node {self.leader_id} is the leader.")
        self.bullystate = "IDLE"

    # util functions for the test

    def leaderfailure(self):
       self.received_leader_heartbeat = False 

    def leaderalive(self):
        self.received_leader_heartbeat = True    

    def test_sendelectionmsg(self,id):
        message = {
                "community_type": "ELECTION",
                "election_type": "ELECTION",
                "peer_uuid": id
            }
        
        self.bully_message_queue.put(message)
            
    def test_sendresponsemsg(self,id):
        message = {
                "community_type": "ELECTION",
                "election_type": "RESPONSE",
                "peer_uuid": id
            }
        
        self.bully_message_queue.put(message)

    def test_sendcoordinatoremsg(self,id):
        message = {
                "community_type": "ELECTION",
                "election_type": "COORDINATOR",
                "peer_uuid": id
            }
        
        self.bully_message_queue.put(message)

    def test_selfid(self,id):
        self.id=id