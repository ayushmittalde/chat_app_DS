
class IdentityLayer:

    def set_reliability_layer(self, reliability_layer):
        from .reliability_layer import ReliabilityLayer
        self.reliability_layer: ReliabilityLayer = reliability_layer
