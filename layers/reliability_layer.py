from collections import deque
import copy
from dataclasses import dataclass
import json
import random
import threading
from typing import Any
import time
"""
No encoding in reliability layer yet
"""

RELIABLE_KEYWORD = "reliable"
UNRELIABLE_KEYWORD = "unreliable"
ACK_KEYWORD = "acknowledgemet"

RECEIVED_PACKAGE_EXPIRATION = 40

class ReliabilityLayer:

    def __init__(self) -> None:
        self.message_id_counter: int = random.randint(0,2**63)
        self.conversations: dict[int,Conversation] = dict()
        self.received_packages: deque[ReceivedPackage] = deque(maxlen=300)
        self.lock = threading.Lock()

    def handle_message(self, message: str):
        decoded_package = json.loads(message)
        # FIXME: Right now we want our own packages back?
        # if decoded_package["sender_uuid"] == str(self.identity_layer.uuid):
        #     # Don't process messages from yourself
        #     return
        rel_type = decoded_package["rel_type"]
        if rel_type == UNRELIABLE_KEYWORD:
            self.community_layer.handle_message(decoded_package["payload"])
        elif rel_type == RELIABLE_KEYWORD:
            self.lock.acquire()
            for received_package in self.received_packages:
                if (received_package.rel_id == decoded_package["rel_id"] and
                        received_package.uuid == decoded_package["sender_uuid"]):
                    if (time.time() < received_package.expires):
                        self.log_event(f"REL {decoded_package['rel_id']} received, duplicate")
                        # Package duplicate received
                        self.lock.release()
                        self._send_ack(decoded_package["sender_uuid"],
                                       decoded_package["rel_id"])
                        return
                    else:
                        self.log_event(f"REL {decoded_package['rel_id']} received, EXPIRED duplicate")
                        # Package duplicate received, but expired
                        self.lock.release()
                        self._deliver_rel_package(decoded_package)
                        return
            # Unseen package received
            self.log_event(f"REL {decoded_package['rel_id']} received, first seen")
            self.lock.release()
            self._deliver_rel_package(decoded_package)
        elif rel_type == ACK_KEYWORD:
            self.log_event(f"ACK {decoded_package['rel_id']} received")
            self._accept_ack(decoded_package["sender_uuid"],
                             decoded_package["rel_id"])
        else:
            self.log_event(f"Received unknown rel_type '{rel_type}'")
          
    def send_unreliably(self,
                        payload: str,
                        destination: str | None,
                        ):
        """Send a package to the destination, fire and forget
        
        Parameters
        ----------
        payload : str
            A string that the destination reliability layer will propagate to
            its community layer via handle_message()
        destination : str | None
            Either the UUID of the destination, or use None to multicast the
            package
        """
        rel_payload = {
            "rel_type": UNRELIABLE_KEYWORD,
            "sender_uuid": str(self.identity_layer.uuid),
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
                      destinations: list[str],
                      tries: int = 15,
                      timeout: float = 1.5,
                      ):
        """Send a package to the destination and make sure everyone got it
        
        Parameters
        ----------
        payload : str
            A string that the destination reliability layer will propagate to
            its community layer via handle_message()
        destination : list[str]
            A list of recipients that are supposed to receive the package
        tries : int
            How many times the package should be resent before giving up
            (default: 15)
        timeout : float
            How many seconds to wait before trying to send the package again
            (default: 1.5)
        """
        if len(destinations) == 0:
            return
        if tries < 1:
            return
        # Generate unique message id
        self.message_id_counter += 1
        reliability_id = self.message_id_counter
        # Store conversation info
        with self.lock:
            self.conversations[reliability_id] = Conversation(
                reliability_id=reliability_id,
                payload=payload,
                destinations_remaining=destinations,
                timeout=timeout,
                tries_left=tries,
            )
        # Start resend loop
        threading.Thread(target=self._reliable_send_loop,
                         args=(reliability_id,),
                         daemon=True,
                         ).start()
    
    def _reliable_send_loop(self, reliability_id: int):
        """Repeatedly send the message until acknowledged"""
        while True:
            self.lock.acquire()
            convo = self.conversations.get(reliability_id, None)
            # If the conversation is already resolved
            if convo is None:
                self.lock.release()
                return
            # If the conversation ran out of tries
            if convo.tries_left <= 0:
                # Clean up info about conversation
                self.conversations.pop(convo.reliability_id)
                self.lock.release()
                return
            # (Re)send message
            convo.tries_left -= 1
            convo_copy = copy.copy(convo)
            self.lock.release()
            rel_payload = {
                "rel_type": RELIABLE_KEYWORD,
                "sender_uuid": str(self.identity_layer.uuid),
                "rel_id": convo_copy.reliability_id,
                "payload": convo_copy.payload,
            }
            encoded_rel_payload = json.dumps(rel_payload)
            if len(convo_copy.destinations_remaining) > 1:
                self.identity_layer.multicast_send(encoded_rel_payload)
            else:
                self.identity_layer.unicast_send(encoded_rel_payload, 
                    convo_copy.destinations_remaining[0])
            self.log_event(f"REL {reliability_id} sent, {convo_copy.tries_left} tries remaining, {len(convo_copy.destinations_remaining)} ACKs remaining")
            # Wait out the timeout
            time.sleep(convo_copy.timeout)
    
    def _deliver_rel_package(self, decoded_package: dict[str,Any]):
        """Deliver the package, send an acknowledgement, and save the package
        in case of later duplicates."""
        # Remember package to prevent duplicates
        with self.lock:
            self.received_packages.append(ReceivedPackage(
                uuid=decoded_package["sender_uuid"],
                rel_id=decoded_package["rel_id"],
                expires= time.time() + RECEIVED_PACKAGE_EXPIRATION,
            ))
        # Send acknowledgement
        self._send_ack(decoded_package["sender_uuid"], decoded_package["rel_id"])
        # Deliver to community layer
        self.community_layer.handle_message(decoded_package["payload"])
    
    def _send_ack(self, target_uuid: str, reliability_id: int):
        """Send an acknowledgement in a separate thread"""
        threading.Thread(target=self._send_ack_this_thread,
                         args=(target_uuid, reliability_id),
                         daemon=True).start()
    
    def _send_ack_this_thread(self, target_uuid: str, reliability_id: int):
        """Send an acknowledgement in this thread"""
        rel_payload = {
            "rel_type": ACK_KEYWORD,
            "sender_uuid": str(self.identity_layer.uuid),
            "rel_id": reliability_id,
        }
        encoded_rel_payload = json.dumps(rel_payload)
        self.identity_layer.unicast_send(encoded_rel_payload, target_uuid)
        self.log_event(f"ACK {reliability_id} sent")
    
    def _accept_ack(self, sender_uuid: str, reliability_id: int):
        """Remove the sender from the list of pending acknowledgers"""
        with self.lock:
            conversation = self.conversations.get(reliability_id, None)
            if conversation is None:
                return
            if sender_uuid in conversation.destinations_remaining:
                conversation.destinations_remaining.remove(sender_uuid)
            # If there are no acknowledgers remaining, forget the conversation
            if len(conversation.destinations_remaining) == 0:
                self.conversations.pop(reliability_id)

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
    payload: str
    destinations_remaining: list[str]
    timeout: float
    tries_left: int

@dataclass
class ReceivedPackage:
    uuid: str
    rel_id: int
    expires: float
