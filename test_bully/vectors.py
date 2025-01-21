import json
import threading
import queue
from functools import cmp_to_key

class VectorClockSystem:
    def __init__(self, node_uuid, participants):
        self.node_uuid = node_uuid
        self.participants = participants

        self.process_message_queue = queue.Queue()
        self.delievered_vc = {uuid: 0 for uuid in participants}
        self.deps_vc=None
        self.hold_back_queue_lock = threading.Lock()
        self.hold_back_queue = []  
        self.seqnummer =0

    def getcopy_hold_back_queue(self):
        with self.hold_back_queue_lock:
            return self.hold_back_queue.copy()
        
    def append_hold_back_queue(self,mess):
        with self.hold_back_queue_lock:
            self.hold_back_queue.append(mess)

    def update_hold_back_queue(self,copy:list):
        with self.hold_back_queue_lock:
            self.hold_back_queue=copy.copy()

    def get_vectorclock_copy(self):
        return self.delievered_vc.copy()
    
    def set_vectorclock_copy(self,x:dict):  #Only called during node initialization
        self.delievered_vc=x.copy()

    def send_message(self, content):
        """Send a message with the updated vector clock."""
        self.deps=self.delievered_vc.copy()
        self.seqnummer+=1
        self.deps[self.node_uuid]=self.seqnummer
        message = {
            "ordering_type": "APPLICATION",
            "content": content,
            "vector_clock": self.deps,
            "sender_uuid": self.node_uuid
        }
        # vector_clock is a dictionary
        self.simulate_network_send(message)

    def handle_message(self, message):
        self.process_message_queue.put(message)
    
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
                if(self.delievered_vc[sender_uuid]>received_vc[sender_uuid]):
                    print("message ignored")
                    pass 
                else :
                    self.append_hold_back_queue(message)

            self.process_hold_back_queue()

    def update_vector_clock(self,sender_uuid):
        """Update the local vector clock after processing the message."""
        self.delievered_vc[sender_uuid]+=1
        print(f"Vector clock {self.delievered_vc}")


    def is_causally_ready(self, message):
        """Check if the message is causally ready for delivery."""
        sender_uuid = message["sender_uuid"]
        received_vc = message["vector_clock"].copy()

        # Perform the below operation :
        # dependency VC received <= delievered_vc
        # where dependency VC received = received_vc[node] (node for all participants != sender_uuid) 
        # received_vc[node]=delievered_vc[node]+1

        if(self.delievered_vc[sender_uuid]+1==received_vc[sender_uuid]):    # Second condition passed (This implements FIFO ordering)
            del received_vc[sender_uuid]                                            # this forms the dependency vector
            for key in list(received_vc.keys()):
                if(received_vc[key]<=self.delievered_vc[key]):              # consistent group views are already implemented
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
        print(f"Printing Sorted hold back queue{copy_hold_back_queue}")

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
        print(f"Delivered: {message}")

    def start(self):
        log_thread = threading.Thread(target=self.process_message, daemon=False)
        log_thread.start()
        


