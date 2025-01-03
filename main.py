import ui.name_input
import ui.leader_yn

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
