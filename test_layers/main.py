import threading
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../layers")))
import ui.name_input
import ui.leader_yn
from layers.application_layer import ApplicationLayer
from layers.community_layer import CommunityLayer
from layers.identity_layer import IdentityLayer
from layers.ordering_layer import OrderingLayer
from layers.reliability_layer import ReliabilityLayer
from layers.ui_layer import UILayer
from layers.config import *

if __name__ == "__main__":

    # Create the layers of our architecture
    ui_layer = UILayer(lambda x: ui_layer.deliver_message("You", x))
    application_layer = ApplicationLayer()
    ordering_layer = OrderingLayer()
    community_layer = CommunityLayer()
    reliability_layer = ReliabilityLayer()
    identity_layer = IdentityLayer()

    # Wire up the layers
    ui_layer.set_application_layer(application_layer)
    application_layer.set_ui_layer(ui_layer)
    application_layer.set_ordering_layer(ordering_layer)
    ordering_layer.set_application_layer(application_layer)
    ordering_layer.set_community_layer(community_layer)
    community_layer.set_ordering_layer(ordering_layer)
    community_layer.set_reliability_layer(reliability_layer)
    reliability_layer.set_community_layer(community_layer)
    reliability_layer.set_identity_layer(identity_layer)
    identity_layer.set_reliability_layer(reliability_layer)

    is_leader = input("Is this node the leader? (yes/no): ").strip().lower() == "yes"

    if(is_leader):
        identity_layer.is_leader=True
        listener_thread = threading.Thread(target=identity_layer.multicast_listen, daemon=False)
        community_layer.start_heartbeat()
        listener_thread.start()
        listener_thread.join()
    else:
        listener_thread = threading.Thread(target=identity_layer.multicast_listen, daemon=False)
        listener_thread.start()
        community_layer.start_heartbeat()
        community_layer.attempt_join()
        listener_thread.join()


