from enum import Enum
import json
import threading

class CommunityLayer:

    def __init__(self, own_name: str, is_leader: bool):
        self.own_name: str = own_name
        self.is_leader: bool = is_leader
        self.state: CommunityLayerState = CommunityLayerState.NOT_CONNECTED
    
    def set_ordering_layer(self, ordering_layer):
        from .ordering_layer import OrderingLayer
        self.ordering_layer: OrderingLayer = ordering_layer

    def set_reliablity_layer(self, reliability_layer):
        from .reliability_layer import ReliabilityLayer
        self.reliablity_layer: ReliabilityLayer = reliability_layer

    def init(self):
        self.reliablity_layer.init()
        if self.is_leader:
            raise NotImplementedError()
        else:
            threading.Thread(target=self._join_group, daemon=True).start()

    def log_event(self, event_message: str):
        self.ordering_layer.log_event(event_message)
    
    def _join_group(self):
        """Attempt to join the group as a peer"""
        self.state = CommunityLayerState.JOINING_GROUP
        packet_content = {
            "packet_type": "want to join",
            "user_name": self.own_name,
        }
        packet_json = json.dumps(packet_content)
        self.reliablity_layer.send_request(
            payload = packet_json,
            convo_id = 0,
            tries = -1, # Try indefinitely
        )



class CommunityLayerState(Enum):
    NOT_CONNECTED = 0
    JOINING_GROUP = 1
    IN_GROUP_AS_PEER = 2
    IN_GROUP_AS_LEADER = 3
