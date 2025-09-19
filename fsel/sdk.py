from typing import Dict, Callable

from picotui.widgets import ACTION_CANCEL, ACTION_OK

from .exit_codes import EXIT_CODE_ENTER, EXIT_CODE_ESCAPE
from .lib.abstract_selection_dialog import AbstractSelectionDialog
from .lib.exit_codes_mapping import KEYS_TO_EXIT_CODES
from .lib.paint_context import p_ctx
from fsel.lib.picotui_patch import patch_picotui

patch_picotui()
from fsel.lib.picotui_patch import *

screen = Screen()


def run_dialog(dialog_supplier: Callable[[int, int, int, int], AbstractSelectionDialog]):
    dialog = None
    try:
        Screen.init_tty()
        Screen.cursor(False)

        screen_width, screen_height = Screen.screen_size()
        cursor_y, cursor_x = cursor_position()
        p_ctx.max_x = screen_width
        p_ctx.max_y = screen_height

        dialog = dialog_supplier(screen_height, screen_width, cursor_y, cursor_x)
        res = dialog.loop()
        exit_code = KEYS_TO_EXIT_CODES.get(res)
        if res == ACTION_OK:
            return EXIT_CODE_ENTER, dialog.items_path()
        elif res == ACTION_CANCEL:
            return EXIT_CODE_ESCAPE, None
        else:
            return exit_code, dialog.items_path()
    finally:
        Screen.attr_reset()
        if dialog is not None:
            dialog.clear()
            Screen.goto(0, dialog.y)

        Screen.cursor(True)
        Screen.deinit_tty()


def full_path(root, rel_path):
    root = root + '/' if root != '/' else '/'
    return root + rel_path


def field_or_else(d: Dict, name, default):
    result = d.get(name)
    if result is None:
        d[name] = result = default
    return result
