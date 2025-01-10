class CommunityLayer:
    
    def set_ordering_layer(self, ordering_layer):
        from .ordering_layer import OrderingLayer
        self.ordering_layer: OrderingLayer = ordering_layer

    def set_reliablity_layer(self, reliability_layer):
        from .reliability_layer import ReliabilityLayer
        self.reliablity_layer: ReliabilityLayer = reliability_layer
