from collections import deque
from dataclasses import dataclass
import json
import random
import threading
import time

class ReliabilityLayer:

    def __init__(self):
        self.message_id_counter: int = random.randint(0,2**63)
        self.unacknowledged_packets: set[int] = set()
        self.conversations: deque[ConversationEntry] = deque(maxlen=300)

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
    
    def send_request(self,
                     payload: str,
                     convo_id: int,
                     destination: tuple[str,int] | None = None,
                     tries: int = 5,
                     ):
        """
        Send a request that expects an answer, not just a plain acknowledgement

        payload: str
            A JSON that the community layer understands
        convo_id: int
            A conversation id chosen by the community layer to be able to tell
            which replies belong to which requests
        destination: tuple[str,int] | None
            Either a IP-adress + port combination for unicast or None for
            multicast
        tries: int
            The number of times this message should be sent maximally. A negative
            number means ininite times, though the packet will expire eventually
            regardless.
        """
        TIMEOUT = 2.0
        if tries == 0:
            return
        # The rel_id identifies this packet for the reliability layer while
        # convo_id identifies it for the community layer. Both id formats have
        # different requirements.
        self.message_id_counter += 1
        rel_id = self.message_id_counter 
        # Assemble nested packet
        packet_content = {
            "rel_id": rel_id,
            "reliability": "request",
            "payload": payload,
        }
        packet_json = json.dumps(packet_content)
        # Store information about packet
        self.conversations.append(ConversationEntry(
            rel_id=rel_id,
            convo_id=convo_id,
            is_request=True,
            payload=packet_json,
            destination=destination,
            individual_timeout=TIMEOUT,
            is_completed=False,
            tries_left=(tries - 1 if tries > 0 else tries),
            expires=time.time()+20,
        ))
        self.unacknowledged_packets.add(rel_id)
        # Send
        if destination is None:
            self.identity_layer.multicast(packet_json)
        else:
            self.identity_layer.unicast(packet_json, destination)
        # Schedule retries
        if tries > 1:
            threading.Thread(target=self._resend_routine, args=(rel_id,), daemon=True)
    
    def _resend_routine(self, rel_id: int):
        """Keep resending packages if they haven't been acknowledged"""
        convo = None
        for target_convo in self.conversations:
            if target_convo.rel_id == rel_id and target_convo.expires > time.time():
                convo = target_convo
                break
        if convo is None:
            self.log_event(f"ERROR: Lost information about rel_id {rel_id:X}")
            return
        
        while True:
            time.sleep(convo.individual_timeout)

            if convo.expires > time.time():
                self.log_event(f"WARNING: Outgoing packet expired: {rel_id:X}")
            if convo.rel_id not in self.unacknowledged_packets:
                convo.is_completed = True
                return
            if convo.tries_left == 0:
                self.log_event(f"WARNING: Giving up on an acknowledgement for packet {rel_id:X}")
                return

            convo.tries_left = convo.tries_left - 1 if convo.tries_left > 0 else convo.tries_left
            if convo.destination is None:
                self.identity_layer.multicast(convo.payload)
            else:
                self.identity_layer.unicast(convo.payload, convo.destination)


@dataclass
class ConversationEntry:
    rel_id: int
    convo_id: int
    is_request: bool
    payload: str
    destination: tuple[str,int] | None
    individual_timeout: float
    is_completed: bool
    tries_left: int
    expires: float
