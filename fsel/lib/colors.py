from fsel.lib.picotui_patch import patch_picotui

patch_picotui()

from picotui.defs import *


class Colors:
    # these are in 256-color mode
    BLACK = C_BLACK
    RED = C_RED
    GREEN = C_GREEN
    YELLOW = 220
    BLUE = 18
    MAGENTA = C_MAGENTA
    CYAN = 31
    WHITE = C_WHITE

    GRAY = 248
    B_RED = 196
    B_GREEN = C_B_GREEN
    B_YELLOW = 227
    B_BLUE = C_B_BLUE
    B_MAGENTA =C_B_MAGENTA
    B_CYAN = C_B_CYAN
    B_WHITE = C_B_WHITE

    C_IDX_BG = 0
    C_IDX_REG_FG = 1
    C_IDX_MATCH_FG = 2

    C_STICKY_FOLDER = [
        # non focused list; non highlighted entry
        [BLACK, B_GREEN, B_RED],
        # non focused list; highlighted entry
        [BLUE, B_GREEN, B_RED],
        # focused list; non highlighted entry
        [BLACK, B_GREEN, B_RED],
        # focused list; highlighted entry
        [CYAN, B_GREEN, B_RED]
    ]

    C_SGID_FOLDER = [
        # non focused list; non highlighted entry
        [BLACK, B_YELLOW, B_RED],
        # non focused list; highlighted entry
        [BLUE, B_YELLOW, B_RED],
        # focused list; non highlighted entry
        [C_BLACK, B_YELLOW, B_RED],
        # focused list; highlighted entry
        [CYAN, B_YELLOW, B_RED]
    ]

    C_SUID_FOLDER = [
        # non focused list; non highlighted entry
        [C_BLACK, (192, 48, 48), (255, 64, 64)],
        # non focused list; highlighted entry
        [BLUE, (192, 48, 48), (255, 64, 64)],
        # focused list; non highlighted entry
        [BLACK, (192, 48, 48), (255, 64, 64)],
        # focused list; highlighted entry
        [CYAN, (192, 48, 48), (255, 64, 64)]
    ]

    C_FOLDER = [
        # non focused list; non highlighted entry
        [BLACK, B_WHITE, B_RED],
        # non focused list; highlighted entry
        [BLUE, B_WHITE, B_RED],
        # focused list; non highlighted entry
        [BLACK, B_WHITE, B_RED],
        # focused list; highlighted entry
        [CYAN, B_WHITE, B_RED]
    ]

    C_LEAF = [
        # non focused list; non highlighted entry
        [BLACK, GRAY, B_RED],
        # non focused list; highlighted entry
        [BLUE, GRAY, B_RED],
        # focused list; non highlighted entry
        [BLACK, GRAY, B_RED],
        # focused list; highlighted entry
        [CYAN, BLACK, B_RED]
    ]


colors = Colors()
