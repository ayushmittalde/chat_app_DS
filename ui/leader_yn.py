import urwid

POSITIVE_ANSWER = "Yes"
NEGATIVE_ANSWER = "No"

def leader_yes_no() -> bool | None:
    is_leader = None

    palette = [
        ("background", "light gray", "black"),
        ("body", "light gray", "black"),
        ("header", "black", "light cyan", "bold"),
        ("button", "dark green", "black", "bold"),
        ("button_focused", "black", "dark green", "bold"),
    ]

    # Handle button press
    def button_pressed(button):
        nonlocal is_leader
        is_leader = (button.get_label() == POSITIVE_ANSWER)
        raise urwid.ExitMainLoop()

    # Build layout
    query_title = urwid.Text("Initialize as leader?")
    query_yes_no = urwid.GridFlow(
        [urwid.AttrMap(urwid.Button(NEGATIVE_ANSWER, button_pressed), "button", "button_focused"),
         urwid.AttrMap(urwid.Button(POSITIVE_ANSWER, button_pressed), "button", "button_focused")],
        7,
        1,
        1,
        urwid.CENTER,
    )
    query_popup = urwid.Pile([query_title, query_yes_no])
    query_popup_outlined = urwid.LineBox(query_popup)
    background = urwid.AttrMap(urwid.SolidFill(), "background")
    body = urwid.Overlay(
        top_w=query_popup_outlined, bottom_w=background, align="center",
        width=23, valign="middle", height="pack",
    )
    header_text = urwid.Text("Decentralized Public Chatroom   F8 to exit")
    header = urwid.AttrMap(header_text, "header")
    frame = urwid.Frame(urwid.AttrMap(body, "body"), header=header)

    # Handle special keypresses
    def unhandled(key: str | tuple[str, int, int, int]) -> None:
        if key == "f8":
            raise urwid.ExitMainLoop()

    urwid.MainLoop(frame, palette, unhandled_input=unhandled).run()
    return is_leader
