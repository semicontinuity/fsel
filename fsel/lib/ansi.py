from picotui.screen import Screen


def attr_underlined(double: bool):
    Screen.wr("\x1b[21m" if double else "\x1b[4m")


def attr_not_underlined():
    Screen.wr("\x1b[24m")


def attr_blinking():
    Screen.wr("\x1b[5m")


def attr_not_blinking():
    Screen.wr("\x1b[25m")
