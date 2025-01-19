class OrderingLayer:

    def set_application_layer(self, application_layer):
        from .application_layer import ApplicationLayer
        self.application_layer: ApplicationLayer = application_layer
    
    def set_community_layer(self, community_layer):
        from .community_layer import CommunityLayer
        self.community_layer: CommunityLayer = community_layer

    def init(self):
        self.community_layer.init()
            
    def log_event(self, event_message: str):
        self.application_layer.log_event(event_message)
        
    def handle_message(self, message: str):
        self.application_layer.deliver_message(message)
