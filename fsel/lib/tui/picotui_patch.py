from picotui.screen import Screen

#################################################################################
# Start patching picotui to use STDERR (FD 2)
#################################################################################
FD_IN = 2
FD_OUT = 2


import os


def wr(*args):
    s = args[-1]
    # TODO: When Python is 3.5, update this to use only bytes
    if isinstance(s, str):
        s = bytes(s, "utf-8")
    os.write(FD_OUT, s)


from picotui.basewidget import Widget
from picotui.defs import KEYMAP as _KEYMAP


def get_input(self):
    if self.kbuf:
        key = self.kbuf[0:1]
        self.kbuf = self.kbuf[1:]
    else:
        key = os.read(FD_IN, 32)
        if key[0] != 0x1b:
            key = key.decode()
            self.kbuf = key[1:].encode()
            key = key[0:1].encode()
    key = _KEYMAP.get(key, key)

    if isinstance(key, bytes) and key.startswith(b"\x1b[M") and len(key) == 6:
        row = key[5] - 33
        col = key[4] - 33
        return [col, row]

    return key


def read_screen_size(*args):
    import select
    res = select.select([FD_IN], [], [], 0.05)[0]
    if not res:
        return 80, 24
    resp = os.read(FD_IN, 32)
    assert resp.startswith(b"\x1b[8;") and resp[-1:] == b"t"
    vals = resp[:-1].split(b";")
    return (int(vals[2]), int(vals[1]))


def screen_size(*args):
    wr(b"\x1b[18t")
    return read_screen_size(args)


def screen_size_or_default(*args):
    size = screen_size()
    if not size:
        return 80, 24
    return size


def cursor_position():
    wr(b"\x1b[6n")
    import select
    res = select.select([FD_IN], [], [], 0.05)[0]
    if not res:
        return None
    s = os.read(FD_IN, 32)
    i1 = s.rfind(b'[')
    i2 = s.index(b';')
    i3 = s.index(b'R')
    return int(s[i1 + 1:i2]) - 1, int(s[i2 + 1:i3]) - 1


def init_tty(*args):
    import tty, termios
    global ttyattr
    ttyattr = termios.tcgetattr(FD_IN)
    tty.setraw(FD_IN)


def deinit_tty(*args):
    import termios
    termios.tcsetattr(FD_IN, termios.TCSANOW, ttyattr)


def patch_picotui(fd_in=2, fd_out=2):
    global FD_IN, FD_OUT
    FD_IN=fd_in
    FD_OUT=fd_out
    Screen.wr = wr
    Screen.init_tty = init_tty
    Screen.deinit_tty = deinit_tty
    Screen.screen_size = screen_size_or_default
    Widget.get_input = get_input

#################################################################################
# End patching picotui
#################################################################################
