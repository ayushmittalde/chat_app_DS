import json
class ApplicationLayer:
    
    def set_ui_layer(self, ui_layer):
        from .ui_layer import UILayer
        self.ui_layer: UILayer = ui_layer
    
    def set_ordering_layer(self, ordering_layer):
        from .ordering_layer import OrderingLayer
        self.ordering_layer: OrderingLayer = ordering_layer

    def init(self):
        self.ordering_layer.init()
    
    def log_event(self, event_message):
        self.ui_layer.log_event(event_message)
    
    def handle_message(self, message):
        data=json.loads(message)

        if (data["ordering_type"]=="UI"):
            self.ui_layer.handle_message(data["content"])
         
    def send_message(self,response):
        data = {
            "ordering_type": "UI",
            "content":response
        }
        self.ordering_layer.send_message(json.dumps(data))
        


