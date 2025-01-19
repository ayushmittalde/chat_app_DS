class ApplicationLayer:
    
    def set_ui_layer(self, ui_layer):
        from .ui_layer import UILayer
        self.ui_layer: UILayer = ui_layer
    
    def set_ordering_layer(self, ordering_layer):
        from .ordering_layer import OrderingLayer
        self.ordering_layer: OrderingLayer = ordering_layer

    def init(self):
        self.ordering_layer.init()
    
    def log_event(self, event_message: str):
        self.ui_layer.log_event(event_message)
    
    def send_message(self, message: str):
        self.ordering_layer.handle_message(message)
        
    def deliver_message(self, message: str):
        data = json.loads(message)
        sender = data.get("sender", "Unknown")
        content = data.get("content", "")
        self.ui_layer.deliver_message(sender, content)


