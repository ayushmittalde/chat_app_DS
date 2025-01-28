import copy
from dataclasses import dataclass
import json
import random
import threading
import time
"""
No encoding in reliability layer yet
"""

REQUEST_KEYWORD = "request"
RESPONSE_KEYWORD = "response"
RELIABLE_KEYWORD = "reliable"
ACK_KEYWORD = "acknowledgemet"
UNRELIABLE_KEYWORD = "unreliable"

class ReliabilityLayer:

    def __init__(self) -> None:
        self.message_id_counter: int = random.randint(0,2**63)
        self.conversations: dict[int,Conversation] = dict()
        self.lock = threading.Lock()

    def handle_message(self, message: str):
        # decoded_message = json.loads(message)
        # rel_type = decoded_message["rel_type"]
        # match rel_type:
        #     case REQUEST_KEYWORD:
        #     case RESPONSE_KEYWORD:
        #     case RELIABLE_KEYWORD:
        msg=json.loads(message)
        self.community_layer.handle_message(msg["payload"])
          
    def send_unreliably(self,
                        payload: str,
                        destination: str | None,
                        ):
        rel_payload = {
            "rel_type": UNRELIABLE_KEYWORD,
            "payload": payload,
        }
        encoded_rel_payload = json.dumps(rel_payload)
        if destination is None:
            self.identity_layer.multicast_send(encoded_rel_payload)
        else:
            self.identity_layer.unicast_send(encoded_rel_payload,
                                                destination)
    
    def send_reliably(self,
                      payload: str,
                      convo_id: int,
                      destination: tuple[str,int] | None,
                      is_request: bool = False,
                      tries: int = 3,
                      timeout: float = 2.0,
                      ):
        # subtract one try
        if tries < 1:
            return
        tries -= 1
        # Generate unique message id
        self.message_id_counter += 1
        reliability_id = self.message_id_counter
        # Store conversation info
        with self.lock:
            self.conversations[reliability_id] = Conversation(
                reliability_id=reliability_id,
                conversation_id=convo_id,
                is_request=is_request,
                payload=payload,
                destination=destination,
                timeout=timeout,
                tries_left=tries,
            )
        # Start resend loop
        threading.Thread(target=self._send_request_loop,
                         args=(reliability_id,),
                         daemon=True,
                         ).start()
    
    def _send_request_loop(self, reliability_id: int):
        while True:
            self.lock.acquire()
            convo = self.conversations.get(reliability_id, None)
            # If the conversation is already resolved
            if convo is None:
                self.lock.release()
                return
            # If the conversation ran out of tries
            if convo.tries_left <= 0:
                convo_id = convo.conversation_id
                # Clean up info about conversation
                self.conversations.pop(convo.reliability_id)
                self.lock.release()
                # Report failure
                self.community_layer.handle_delivery_failure(convo_id)
                return
            # (Re)send message
            convo.tries_left -= 1
            convo_copy = copy.copy(convo)
            self.lock.release()
            rel_payload = {
                "rel_type": (REQUEST_KEYWORD if convo_copy.is_request 
                             else RELIABLE_KEYWORD),
                "rel_id": convo_copy.reliability_id,
                "payload": convo_copy.payload,
            }
            encoded_rel_payload = json.dumps(rel_payload)
            if convo_copy.destination is None:
                self.identity_layer.multicast_send(encoded_rel_payload)
            else:
                self.identity_layer.unicast_send(encoded_rel_payload, 
                                                    convo_copy.destination)
            # Wait out the timeout
            time.sleep(convo_copy.timeout)
    
    # def _send_acknowledgement(self, reliability_id: int):


    def set_community_layer(self, community_layer):
        from .community_layer import CommunityLayer
        self.community_layer: CommunityLayer = community_layer
    
    def set_identity_layer(self, identity_layer):
        from .identity_layer import IdentityLayer
        self.identity_layer: IdentityLayer = identity_layer

    def init(self):
        self.identity_layer.init()
            
    def log_event(self, event_message: str):
        self.community_layer.log_event(event_message)

@dataclass
class Conversation:
    reliability_id: int
    conversation_id: int
    is_request: bool
    payload: str
    destination: tuple[str,int] | None
    timeout: float
    tries_left: int
