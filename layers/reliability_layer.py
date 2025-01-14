import json
"""
No encoding in reliability layer yet
"""
class ReliabilityLayer:
    def handle_message(self, message, addr):
         self.community_layer.handle_message(message, addr)

    def send_response(self,response):
        self.identity_layer.broadcast_message(response)

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
