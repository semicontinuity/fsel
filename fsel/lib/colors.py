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
    B_MAGENTA = C_B_MAGENTA
    B_CYAN = C_B_CYAN
    B_WHITE = C_B_WHITE

    C_IDX_BG = 0
    C_IDX_REG_FG = 1
    C_IDX_MATCH_FG = 2
