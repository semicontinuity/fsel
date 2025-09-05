from .picotui_patch import patch_picotui

patch_picotui()

from picotui.defs import *


class Colors:
    BLUE = 18
    B_YELLOW = 227
    B_GREEN = 120
    B_RED = 196
    GRAY = 248
    CYAN = 31
    YELLOW = 220  # Yellow color for descriptions

    C_IDX_BG = 0
    C_IDX_REG_FG = 1
    C_IDX_MATCH_FG = 2

    C_STICKY_FOLDER = [
        # non focused list; non highlighted entry
        [C_BLACK, B_GREEN, C_B_RED],
        # non focused list; highlighted entry
        [BLUE, B_GREEN, C_B_RED],
        # focused list; non highlighted entry
        [C_BLACK, B_GREEN, C_B_RED],
        # focused list; highlighted entry
        [CYAN, B_GREEN, C_B_RED]
    ]

    C_SGID_FOLDER = [
        # non focused list; non highlighted entry
        [C_BLACK, B_YELLOW, C_B_RED],
        # non focused list; highlighted entry
        [BLUE, B_YELLOW, C_B_RED],
        # focused list; non highlighted entry
        [C_BLACK, B_YELLOW, C_B_RED],
        # focused list; highlighted entry
        [CYAN, B_YELLOW, C_B_RED]
    ]

    C_SUID_FOLDER = [
        # non focused list; non highlighted entry
        [C_BLACK, (192, 48, 48), (255, 64, 64)],
        # non focused list; highlighted entry
        [BLUE, (192, 48, 48), (255, 64, 64)],
        # focused list; non highlighted entry
        [C_BLACK, (192, 48, 48), (255, 64, 64)],
        # focused list; highlighted entry
        [CYAN, (192, 48, 48), (255, 64, 64)]
    ]

    C_FOLDER = [
        # non focused list; non highlighted entry
        [C_BLACK, C_B_WHITE, C_B_RED],
        # non focused list; highlighted entry
        [BLUE, C_B_WHITE, C_B_RED],
        # focused list; non highlighted entry
        [C_BLACK, C_B_WHITE, C_B_RED],
        # focused list; highlighted entry
        [CYAN, C_B_WHITE, C_B_RED]
    ]

    C_LEAF = [
        # non focused list; non highlighted entry
        [C_BLACK, GRAY, C_B_RED],
        # non focused list; highlighted entry
        [BLUE, GRAY, C_B_RED],
        # focused list; non highlighted entry
        [C_BLACK, GRAY, C_B_RED],
        # focused list; highlighted entry
        [CYAN, C_BLACK, C_B_RED]
    ]


colors = Colors()
