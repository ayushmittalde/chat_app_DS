import threading
import time

import ui.name_input
import ui.leader_yn
import ui.chat_ui

def generate_events(chat_ui):
    counter = 1
    while True:
        chat_ui.add_event(f"This is event {counter}!")
        counter += 1
        time.sleep(0.5)

def generate_messages(chat_ui):
    counter = 1
    while True:
        chat_ui.deliver_message("Booper", "BOOP")
        counter += 1
        time.sleep(3.3)

if __name__ == "__main__":
    # TODO: Integrate the username querying into a single UI system
    # Query the user for an user name
    username = ui.name_input.user_input_name()
    if username is None:
        exit()
    
    # Query the user whether to initialize as a leader
    is_leader = ui.leader_yn.leader_yes_no()
    if is_leader is None:
        exit()

    chat_ui = ui.chat_ui.ChatUI(lambda x: chat_ui.deliver_message("You", x))
    event_generator = threading.Thread(target=generate_events, args=(chat_ui,), daemon=True)
    event_generator.start()
    chat_generator = threading.Thread(target=generate_messages, args=(chat_ui,), daemon=True)
    chat_generator.start()
    chat_ui.start()
