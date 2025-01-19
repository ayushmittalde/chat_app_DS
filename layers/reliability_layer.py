import json
"""
No encoding in reliability layer yet
"""
class ReliabilityLayer:
    def handle_message(self, message: str):
         self.community_layer.handle_message(message)
         
    def send_message(self, message: str):
        self.identity_layer.send_message(message)

    def send_response(self,response):
        self.identity_layer.send_message(response)

    def broadcast_elecmsg(self,response,id):
        self.identity_layer.broadcast_elecmsg(response,id)

    def send_heartbeat(self,response):
        self.identity_layer.broadcast_heartbeat(response)

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
