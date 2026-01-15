from picotui.basewidget import ACTION_CANCEL, ACTION_OK
from picotui.defs import KEY_QUIT, KEY_ESC, KEY_ENTER

from .abstract_selection_dialog import AbstractSelectionDialog
from .custom_list_box import CustomListBox
from fsel.lib.list_item_info_service import list_item_info_service


class ItemSelectionDialog(AbstractSelectionDialog):
    def __init__(self, screen_height, width, height, x, y, items):
        super().__init__(screen_height, 0, 0, width, height)
        self.x = x
        self.y = y
        self.request_height(len(items))
        self.add(0, 0, CustomListBox(list_item_info_service.max_item_text_length(items), len(items), items))

    def handle_key(self, key):
        if key == KEY_QUIT:
            return KEY_QUIT
        if key == KEY_ESC and self.finish_on_esc:
            return ACTION_CANCEL
        elif self.focus_w:
            if key == KEY_ENTER:
                return ACTION_OK
            return self.focus_w.handle_key(key)

    def items_path(self):
        return [self.focus_w.items[self.focus_w.cur_line]]
