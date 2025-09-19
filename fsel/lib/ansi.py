from picotui.screen import Screen


def attr_color(fg, bg=-1):
    if bg == -1:
        bg = fg >> 4
        fg &= 0xf

    if type(fg) is tuple:
        r, g, b = fg
        s = "\x1b[38;2;%d;%d;%d;" % (r, g, b)
    else:
        s = "\x1b[38;5;%d;" % (fg,)
    if type(bg) is tuple:
        r, g, b = bg
        s += "48;2;%d;%d;%dm" % (r, g, b)
    else:
        s += "48;5;%dm" % (bg,)

    Screen.wr(s)


def attr_underlined(double: bool):
    Screen.wr("\x1b[21m" if double else "\x1b[4m")


def attr_not_underlined():
    Screen.wr("\x1b[24m")


def attr_italic(on: bool):
    Screen.wr("\x1b[3m" if on else "\x1b[23m")


def attr_strike_thru(on: bool):
    Screen.wr("\x1b[9m" if on else "\x1b[29m")


def attr_reversed():
    Screen.wr("\x1b[7m")


def attr_not_reversed():
    Screen.wr("\x1b[27m")


def attr_blinking():
    Screen.wr("\x1b[5m")


def attr_not_blinking():
    Screen.wr("\x1b[25m")


def attr_crossed_out():
    Screen.wr("\x1b[9m")


def attr_not_crossed_out():
    Screen.wr("\x1b[29m")
