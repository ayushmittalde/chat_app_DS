from collections import deque
import urwid

FRAME_UPDATE_INTERVAL = 0.5

class ChatUI:

    def __init__(self):
        self.events_shown = False
        self.autoscroll = True
        self.event_log: deque[str] = deque(maxlen=300)
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
        header_text = urwid.Text("Decentralized Public Chatroom   F2 for event log   F8 to exit")
        header = urwid.AttrMap(header_text, "header")
        message_input = urwid.Edit(caption=">")
        footer = urwid.AttrMap(message_input, "footer")
        chat = urwid.Text(
            "Booper: I get you man, I'm not sure how I've resisted murdering the neighbors in my last apartment\n"
            "Booper: Hah, I'd like to see that\n"
            "Thatcher: One day I'll glue my subwoofer to the ceiling and have it randomly play dubstep songs at night\n"
            "Booper: rip\n"
            "Thatcher: I think my upstairs neighbors are testing the jackhammer they got for christmas\n"
            "Booper: What's keeping you up?\n"
            "Thatcher: Yeah, can't sleep\n"
            "Booper: You up?\n"
        )
        scroll_chat = urwid.AttrMap(urwid.ScrollBar(urwid.Scrollable(chat)), "body")
        status = urwid.AttrMap(urwid.Text("Not connected"), "status")
        self.status_chat = urwid.Frame(body=scroll_chat, header=status)
        self.events_text = urwid.Text(list(self.event_log))
        self.scroll_events = urwid.AttrMap(urwid.ScrollBar(urwid.Scrollable(self.events_text)), "events")
        self.body = urwid.Columns([self.status_chat])
        self.frame = urwid.Frame(body=self.body, header=header, footer=footer)

    def _unhandled(self, key: str | tuple[str, int, int, int]) -> None:
        if key == "f2":
            self.events_shown = not self.events_shown
            if self.events_shown:
                self.body.contents = [(self.status_chat, ("weight", 1, False)), (self.scroll_events, ("weight", 1, False))]
            else:
                self.body.contents = [(self.status_chat, ("weight", 1, False))]
        elif key == "f3":
            self.autoscroll = not self.autoscroll
        elif key == "f8":
            raise urwid.ExitMainLoop()
    
    def add_event(self, event_message: str):
        self.event_log.append("$ " + event_message + "\n")
        self.events_text.set_text(list(reversed(self.event_log)))

    def refresh_screen_loop(self, loop, user_data: str):
        """Makes sure the screen updates even when not in focus."""
        self.main_loop.draw_screen()
        self.main_loop.set_alarm_in(FRAME_UPDATE_INTERVAL, self.refresh_screen_loop)
        
    def start(self):
        self.main_loop = urwid.MainLoop(self.frame, self.palette, unhandled_input=self._unhandled)
        self.main_loop.set_alarm_in(FRAME_UPDATE_INTERVAL, self.refresh_screen_loop)
        self.main_loop.run()
