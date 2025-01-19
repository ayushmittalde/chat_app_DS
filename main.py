import threading
import time
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "./layers")))

import ui.name_input
import ui.leader_yn
from layers.application_layer import ApplicationLayer
from layers.community_layer import CommunityLayer
from layers.identity_layer import IdentityLayer
from layers.ordering_layer import OrderingLayer
from layers.reliability_layer import ReliabilityLayer
from layers.ui_layer import UILayer

def generate_events(chat_ui):
    counter = 1
    while True:
        chat_ui.log_event(f"This is event {counter}!")
        counter += 1
        time.sleep(0.5)

def generate_messages(chat_ui, username):
    counter = 1
    while True:
        #chat_ui.deliver_message("Booper", "BOOP")
        chat_ui.deliver_message(username, f"Message {counter}")
        counter += 1
        time.sleep(3.3)

if __name__ == "__main__":
    # TODO: Integrate the username querying into a single UI system
    # Query the user for an user name
    username = ui.name_input.user_input_name()
    if username is None:
        exit()
            
    # Create the UI layer and pass the username
    ui_layer = UILayer(username=username)


    # Create the layers of our architecture
    #ui_layer = UILayer(lambda x: ui_layer.deliver_message("You", x))
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
    community_layer.set_reliablity_layer(reliability_layer)
    reliability_layer.set_community_layer(community_layer)
    reliability_layer.set_identity_layer(identity_layer)
    identity_layer.set_reliability_layer(reliability_layer)

    #event_generator = threading.Thread(target=generate_events, args=(ui_layer,), daemon=True)
    #event_generator.start()
    #chat_generator = threading.Thread(target=generate_messages, args=(ui_layer, username), daemon=True)
    #chat_generator.start()
    ui_layer.start()
