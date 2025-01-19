import json
class OrderingLayer:

    def handle_message(self, message):
        data=json.loads(message)

        if (data["ordering_type"]=="APPLICATION"):
            self.application_layer.handle_message(data["content"])
         
    def send_message(self,response):
        data = {
            "ordering_type": "APPLICATION",
            "content":response
        }
        self.community_layer.send_message(json.dumps(data))

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
