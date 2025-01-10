class ApplicationLayer:
    
    def set_ui_layer(self, ui_layer):
        from .ui_layer import UILayer
        self.ui_layer: UILayer = ui_layer
    
    def set_ordering_layer(self, ordering_layer):
        from .ordering_layer import OrderingLayer
        self.ordering_layer: OrderingLayer = ordering_layer
