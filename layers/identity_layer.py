
class IdentityLayer:

    def set_reliability_layer(self, reliability_layer):
        from .reliability_layer import ReliabilityLayer
        self.reliability_layer: ReliabilityLayer = reliability_layer

    def init(self):
        pass
        
    def _log_event(self, event_message: str):
        self.reliability_layer.log_event(event_message)

    def multicast(self, payload: str):
        raise NotImplementedError()
    
    def unicast(self, payload: str, destination: tuple[str,int]):
        raise NotImplementedError()
