class OrderingLayer:

    def set_application_layer(self, application_layer):
        from .application_layer import ApplicationLayer
        self.application_layer: ApplicationLayer = application_layer
    
    def set_community_layer(self, community_layer):
        from .community_layer import CommunityLayer
        self.community_layer: CommunityLayer = community_layer
