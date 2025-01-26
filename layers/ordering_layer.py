import json
import threading
import queue
from functools import cmp_to_key
from layers.config import shared_data_instance
import time

class OrderingLayer:
    def __init__(self):
        self.node_uuid=""
        self.process_message_queue = queue.Queue()
        self.vc_lock = threading.Lock()
        self.delievered_vc = {}
        self.deps_vc=None
        self.hold_back_queue_lock = threading.Lock()
        self.hold_back_queue = []  
        self.seqnummer =0
        self.log_message_queue = queue.Queue()

        # Lock for the log function
        self.log_lock = threading.Lock()

    def getcopy_hold_back_queue(self):
        with self.hold_back_queue_lock:
            return self.hold_back_queue.copy()
        
    def append_hold_back_queue(self,mess):
        with self.hold_back_queue_lock:
            self.hold_back_queue.append(mess)

    def update_hold_back_queue(self,copy:list):
        with self.hold_back_queue_lock:
            self.hold_back_queue=copy.copy()
            self.printk("ORD",str(self.hold_back_queue))

    def get_vectorclock_copy(self):
        with self.vc_lock:
            return self.delievered_vc.copy()
    
    def int_vectorclock_seqnum(self,x:dict):  #Only called during node initialization, please do not call this function anywhere else , it resets the sequence number also
        with self.vc_lock:
            self.delievered_vc=x.copy()
            self.seqnummer=0            
            self.printk("ORD",str(self.delievered_vc))
    
    def set_vectorclock_element(self, key, value):
        with self.vc_lock:
            self.delievered_vc[key] = value

    def get_vectorclock_element(self, key):
        with self.vc_lock:
            try:
                return self.delievered_vc[key]
            except KeyError:
                self.printk("ORD",f"KeyError: The key '{key}' was not found in delievered_vc.")
                self.printk("ORD",f"Vector clock {str(self.delievered_vc)}")
                self.printk("ORD",f"Group View {str(self.community_layer.get_groupview_copy())}")
                return -2

    def handle_message(self, message):
        data=json.loads(message)
        self.process_message_queue.put(data)

    def send_message(self,response):
        self.deps=self.get_vectorclock_copy()
        self.seqnummer+=1
        self.deps[self.node_uuid]=self.seqnummer
        message = {
            "ordering_type": "APPLICATION",
            "content": response,
            "vector_clock": self.deps,
            "sender_uuid": self.node_uuid
        }
        self.community_layer.send_message(json.dumps(message))

    def replay_holdbackqueue(self):
        holdback_thread = threading.Thread(target=self.holdbackqueureplay, daemon=True)
        holdback_thread.start()

    def holdbackqueureplay(self):
        time.sleep(0.5)
        x=self.getcopy_hold_back_queue()
        for val in x:
            self.community_layer.send_message(json.dumps(val))
            time.sleep(0.1)
    
    def process_message(self):
        while True:
            message=self.process_message_queue.get()
            """Process an incoming message with vector clock validation."""

            # Check if the message can be delivered BEFORE updating the local vector clock
            if self.is_causally_ready(message):
                self.deliver_message(message["content"])
                self.update_vector_clock(message["sender_uuid"])
            else:
                sender_uuid = message["sender_uuid"]
                received_vc = message["vector_clock"].copy()
                if(self.get_vectorclock_element(sender_uuid)>received_vc[sender_uuid]):
                    self.printk("ORD","message ignored")
                    pass 
                else :
                    self.append_hold_back_queue(message)

            self.process_hold_back_queue()

    def update_vector_clock(self,sender_uuid):
        """Update the local vector clock after processing the message."""
        with self.vc_lock:
            self.delievered_vc[sender_uuid]+=1
            self.printk("ORD",f"Vector clock {self.delievered_vc}")

    def is_causally_ready(self, message):
        """Check if the message is causally ready for delivery."""
        sender_uuid = message["sender_uuid"]
        received_vc = message["vector_clock"].copy()

        # Perform the below operation :
        # dependency VC received <= delievered_vc
        # where dependency VC received = received_vc[node] (node for all participants != sender_uuid) 
        # received_vc[node]=delievered_vc[node]+1

        
        if(self.get_vectorclock_element(sender_uuid)+1==received_vc[sender_uuid]):    # Second condition passed (This implements FIFO ordering)
            del received_vc[sender_uuid]                                            # this forms the dependency vector
            for key in list(received_vc.keys()):
                if(received_vc[key]<=self.get_vectorclock_element(key)):              # consistent group views are already implemented
                    pass
                else :
                    return False                                            # Some messages are lost
            return True
        else :
            return False
    
    def compare(self,a, b):  # function used to sort hold back queue
        vc1=a["vector_clock"]
        vc2=b["vector_clock"]

        for key in list(vc1.keys()):
            if(vc1[key]<=vc2[key]):              # consistent group views are already implemented
                pass
            else :
                return 1

        return -1

    def process_hold_back_queue(self):
        """Process the hold-back queue and deliver causally ready messages."""
        remaining_messages = []

        copy_hold_back_queue=self.getcopy_hold_back_queue()

        # sort the messages in ascending vector clocks
        copy_hold_back_queue=sorted(copy_hold_back_queue, key=cmp_to_key(self.compare))
        self.printk("ORD",f"Printing Sorted hold back queue{copy_hold_back_queue}")

        # Try to deliver messages in the hold-back queue
        for message in copy_hold_back_queue:
            if self.is_causally_ready(message):
                self.deliver_message(message["content"])
                self.update_vector_clock(message["sender_uuid"])
            else:
                remaining_messages.append(message)

        # Replace hold-back queue with undelivered messages
        self.update_hold_back_queue(remaining_messages)

    def deliver_message(self, message):
        """Deliver the message and update the log."""
        #print(message)
        self.application_layer.handle_message(message)

    def set_application_layer(self, application_layer):
        from .application_layer import ApplicationLayer
        self.application_layer: ApplicationLayer = application_layer
    
    def set_community_layer(self, community_layer):
        from .community_layer import CommunityLayer
        self.community_layer: CommunityLayer = community_layer

    def init(self):
        self.node_uuid=str(self.community_layer.reliablity_layer.identity_layer.uuid)
        self.community_layer.init()

        log_thread = threading.Thread(target=self.recv_log, daemon=True)
        log_thread.start()

        log_thread = threading.Thread(target=self.process_message, daemon=True)
        log_thread.start()
        
    def printk(self,type,message):
        self.log_message_queue.put((type,message))

    def recv_log(self):
        while True:
            type,message=self.log_message_queue.get()
            if type=="ORD" and shared_data_instance.ORDERING ==True:
                self.log_event(message)

    def log_event(self, event_message: str):
        with self.log_lock:
            self.application_layer.log_event(event_message)

    def test_send_dummymessage(self,response):
        self.deps=self.get_vectorclock_copy()
        self.seqnummer+=1
        self.deps[self.node_uuid]=self.seqnummer
        message = {
            "ordering_type": "APPLICATION",
            "content": response,
            "vector_clock": self.deps,
            "sender_uuid": self.node_uuid
        }
        return message