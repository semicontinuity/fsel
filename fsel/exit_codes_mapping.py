#!/usr/bin/env python3

from picotui.defs import *
from .picotui_keys import *
from .exit_codes import *


KEYS_TO_EXIT_CODES = {
    KEY_DELETE: EXIT_CODE_DELETE,
    KEY_ESC: EXIT_CODE_ESCAPE,
    KEY_INSERT: EXIT_CODE_INSERT,
    KEY_ALT_INSERT: (EXIT_CODE_ALT + EXIT_CODE_INSERT),
    KEY_ENTER: EXIT_CODE_ENTER,
    KEY_ALT_ENTER: (EXIT_CODE_ALT + EXIT_CODE_ENTER),
    KEY_BACKSPACE: EXIT_CODE_BACKSPACE,

    KEY_CTRL_SPACE: EXIT_CODE_CTRL_SPACE,
    KEY_CTRL_ALT_SPACE: EXIT_CODE_CTRL_ALT_SPACE,
    KEY_ALT_SHIFT_SPACE: EXIT_CODE_ALT_SHIFT_SPACE,

    KEY_F1: EXIT_CODE_F1,
    KEY_CTRL_F1: (EXIT_CODE_CTRL + EXIT_CODE_F1),

    KEY_F2: EXIT_CODE_F2,
    KEY_CTRL_F2: (EXIT_CODE_CTRL + EXIT_CODE_F2),

    KEY_F3: EXIT_CODE_F3,
    KEY_SHIFT_F3: (EXIT_CODE_SHIFT + EXIT_CODE_F3),
    KEY_ALT_F3: (EXIT_CODE_ALT + EXIT_CODE_F3),
    KEY_ALT_SHIFT_F3: (EXIT_CODE_ALT + EXIT_CODE_SHIFT + EXIT_CODE_F3),
    KEY_CTRL_F3: (EXIT_CODE_CTRL + EXIT_CODE_F3),

    KEY_F4: EXIT_CODE_F4,
    KEY_CTRL_F4: (EXIT_CODE_CTRL + EXIT_CODE_F4),

    KEY_F5: EXIT_CODE_F5,
    KEY_CTRL_F5: (EXIT_CODE_CTRL + EXIT_CODE_F5),

    KEY_F6: EXIT_CODE_F6,
    KEY_ALT_F6: (EXIT_CODE_ALT + EXIT_CODE_F6),
    KEY_SHIFT_F6: (EXIT_CODE_SHIFT + EXIT_CODE_F6),
    KEY_CTRL_F6: (EXIT_CODE_CTRL + EXIT_CODE_F6),

    KEY_F7: EXIT_CODE_F7,
    KEY_CTRL_F7: (EXIT_CODE_CTRL + EXIT_CODE_F7),

    KEY_F8: EXIT_CODE_F8,
    KEY_CTRL_F8: (EXIT_CODE_CTRL + EXIT_CODE_F8),

    KEY_F9: EXIT_CODE_F9,
    KEY_CTRL_F9: (EXIT_CODE_CTRL + EXIT_CODE_F9),

    KEY_F10: EXIT_CODE_F10,
    KEY_SHIFT_F10: (EXIT_CODE_SHIFT + EXIT_CODE_F10),
    KEY_CTRL_F10: (EXIT_CODE_CTRL + EXIT_CODE_F10),

    KEY_CTRL_F11: (EXIT_CODE_CTRL + EXIT_CODE_F11),
    KEY_CTRL_F12: (EXIT_CODE_CTRL + EXIT_CODE_F12),
}
