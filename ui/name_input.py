import urwid

MAX_USERNAME_LEN = 16

# Derived from: https://www.reddit.com/r/commandline/comments/14hv1lv/with_urwid_is_it_possible_to_limit_the_width_of/?rdt=56382
class FixedEdit(urwid.Edit):
  """Edit widget with limited amount of allowed characters"""
  def __init__(self, max_cols):
    self.max_cols = max_cols
    super().__init__()

  def keypress(self, size, key):
    if key in ["delete","backspace","left","right","enter"]:
      return super().keypress(size, key)
    else:
      posttext = super().edit_text 
      if len(posttext) < self.max_cols: 
        return super().keypress(size, key)
    return None

def user_input_name() -> str | None:
    selected_username = None

    palette = [
        ("background", "light gray", "black"),
        ("body", "light gray", "black"),
        ("header", "black", "light cyan", "bold"),
    ]

    # Build layout
    query_title = urwid.Text("Pick a username:")
    query_edit = FixedEdit(max_cols=MAX_USERNAME_LEN)
    query_popup = urwid.Pile([query_title, query_edit])
    query_popup_outlined = urwid.LineBox(query_popup)
    background = urwid.AttrMap(urwid.SolidFill(), "background")
    body = urwid.Overlay(
       top_w=query_popup_outlined, bottom_w=background, align="center",
       width=20, valign="middle", height="pack",
    )
    header_text = urwid.Text("Decentralized Public Chatroom   F8 to exit")
    header = urwid.AttrMap(header_text, "header")
    frame = urwid.Frame(urwid.AttrMap(body, "body"), header=header)

    # Handle special keypresses
    def unhandled(key: str | tuple[str, int, int, int]) -> None:
        if key == "f8":
            raise urwid.ExitMainLoop()
        elif key == "enter":
            nonlocal selected_username
            username = query_edit.get_edit_text()
            if len(username) > MAX_USERNAME_LEN or len(username) <= 0:
               # Ignore invalid inputs
               return
            selected_username = username
            raise urwid.ExitMainLoop()

    urwid.MainLoop(frame, palette, unhandled_input=unhandled).run()
    return selected_username