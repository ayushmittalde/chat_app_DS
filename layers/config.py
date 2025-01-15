class SharedData:
    def __init__(self):
        self.GROUP_ADDRESS = "224.0.0.10"
        self.GROUP_PORT = 55000
        self.HEARTBEAT_INT=2 # milli second
        self.HEARTBEAT_TIMEOUT=5
        self.DEBUG =True    
        
shared_data_instance = SharedData()

#Message Types
"""
Community type :
message={
        "community_type": "WANT_TO_JOIN",
        "peer_uuid": str(self.reliablity_layer.identity_layer.uuid)
        }

response = {
    "community_type": "WANT_TO_JOIN_RESPONSE",
    "last_messages": self.message_history[-20:],
    "participants": self.group_participants
}

beat = {
"community_type": "HEARTBEAT",
"peer_uuid": str(self.reliablity_layer.identity_layer.uuid)
}
"""



