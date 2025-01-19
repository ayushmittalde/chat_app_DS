from collections import deque
from typing import Callable
import urwid

FRAME_UPDATE_INTERVAL = 0.5

class UILayer:

    def __init__(self, send_message: Callable[[str], None], username: str):
        """The send_message function will be called each time the user submits a message"""
        self.username = username  # Store the username
        self.events_shown = False
        self.event_log: deque[str] = deque(maxlen=300)
        self.chat_log: deque[str] = deque(maxlen=300)
        self.status_msg: str = "Not connected"
        self.send_message: Callable[[str], None] = send_message
        self._setup_ui()

    def _setup_ui(self):
        self.palette = [
            ("body", "light gray", "black"),
            ("own_message", "light green", "black"),
            ("header", "black", "light cyan", "bold"),
            ("footer", "white", "light magenta", "bold"),
            ("events", "black", "light green"),
            ("status", "light gray", "dark blue"),
        ]
        ui_header_text = urwid.Text("Decentralized Public Chatroom   F2 for event log   F8 to exit")
        ui_header = urwid.AttrMap(ui_header_text, "header")
        self.ui_message_input = urwid.Edit(caption=">")
        ui_footer = urwid.AttrMap(self.ui_message_input, "footer")
        self.ui_chat_text = urwid.Text("")
        ui_scroll_chat = urwid.AttrMap(urwid.ScrollBar(urwid.Scrollable(self.ui_chat_text)), "body")
        self.ui_status_text = urwid.Text(self.status_msg)
        self.ui_status_chat = urwid.Frame(body=ui_scroll_chat, header=urwid.AttrMap(self.ui_status_text, "status"))
        self.ui_events_text = urwid.Text(list(self.event_log))
        self.ui_scroll_events = urwid.AttrMap(urwid.ScrollBar(urwid.Scrollable(self.ui_events_text)), "events")
        self.ui_body = urwid.Columns([self.ui_status_chat])
        self.ui_frame = urwid.Frame(body=self.ui_body, header=ui_header, footer=ui_footer)
    
    def set_application_layer(self, application_layer):
        from .application_layer import ApplicationLayer
        self.application_layer: ApplicationLayer = application_layer

    def _unhandled(self, key: str | tuple[str, int, int, int]) -> None:
        if key == "f2":
            self.events_shown = not self.events_shown
            if self.events_shown:
                self.ui_body.contents = [(self.ui_status_chat, ("weight", 1, False)), (self.ui_scroll_events, ("weight", 1, False))]
            else:
                self.ui_body.contents = [(self.ui_status_chat, ("weight", 1, False))]
        elif key == "f8":
            raise urwid.ExitMainLoop()
        elif key == "enter":
            message = self.ui_message_input.get_edit_text()
            if len(message) > 0:
                self.ui_message_input.set_edit_text("")
                self.send_message(message)
    
    def send_message(self, content: str):
        message = {
            "type": "chat",
            "sender": self.username,
            "content": content
        }
        self.application_layer.send_message(json.dumps(message))
    
    def log_event(self, event_message: str):
        """Add this message to the UI's event log"""
        self.event_log.append("$ " + event_message + "\n")
        self.ui_events_text.set_text(list(reversed(self.event_log)))
    
    def deliver_message(self, sender_name: str, message_text: str):
        """Add this message to the UI's chat log"""
        # Check if the sender is the current user
        display_name = "You" if sender_name == self.username else sender_name

        # Add the message with the sender's name to the chat log
        self.chat_log.append(f"{display_name}: {message_text}\n")
        self.ui_chat_text.set_text(list(reversed(self.chat_log)))
    
    def set_status(self, status_msg: str):
        """Replace the UI's status text with this message"""
        self.status_msg = status_msg
        self.ui_status_text.set_text(self.status_msg)

    def _refresh_screen_loop(self, loop, user_data: str):
        """Makes sure the screen updates even when not in focus."""
        self.main_loop.draw_screen()
        self.main_loop.set_alarm_in(FRAME_UPDATE_INTERVAL, self._refresh_screen_loop)
        
    def start(self):
        self.application_layer.init()
        self.main_loop = urwid.MainLoop(self.ui_frame, self.palette, unhandled_input=self._unhandled)
        self.main_loop.set_alarm_in(FRAME_UPDATE_INTERVAL, self._refresh_screen_loop)
        self.main_loop.run()
