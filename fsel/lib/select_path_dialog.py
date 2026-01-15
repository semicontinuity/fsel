from typing import Optional, List, Dict, Tuple

from picotui.basewidget import ACTION_CANCEL, ACTION_OK
from picotui.defs import KEY_QUIT, KEY_ESC, KEY_SHIFT_TAB, KEY_ENTER, KEY_TAB, KEY_RIGHT, KEY_LEFT, KEY_HOME, KEY_END, \
    KEY_UP, KEY_DOWN, KEY_PGUP, KEY_PGDN, KEY_DELETE, KEY_BACKSPACE
from picotui.widgets import WListBox

from .abstract_selection_dialog import AbstractSelectionDialog
from .custom_list_box import CustomListBox
from .exit_codes_mapping import KEYS_TO_EXIT_CODES
from .keys import KEY_ALT_UP, KEY_ALT_DOWN, KEY_ALT_PAGE_UP, KEY_ALT_PAGE_DOWN, KEY_ALT_RIGHT, KEY_ALT_LEFT
from .list_boxes import ListBoxes
from .list_item_info_service import list_item_info_service
from .logging import debug
from fsel.lib.tui.picotui_keys import KEY_ALT_HOME


class SelectPathDialog(AbstractSelectionDialog):
    def __init__(self, folder_lists: ListBoxes, screen_width, screen_height, width, height, x, y):
        super().__init__(screen_height, x, y, width, height)
        self.screen_width = screen_width
        self.folder_lists = folder_lists
        folder_lists.expand_lists()
        self.layout()
        self.make_focused_column_visible(True)

    def layout(self):
        debug("SelectPathDialog.layout", boxes_length=len(self.folder_lists.boxes))
        self.request_height(self.folder_lists.max_child_height())
        self.childs = []
        child_x = 0

        for i, child in enumerate(self.folder_lists.boxes):
            child.h = child.height = min(len(child.items), self.h)
            self.add(child_x, 0, child)
            child_x += child.width + 1
            if child.focus:
                debug("SelectPathDialog.layout", focus=child)
                self.focus_w = child
                self.focus_idx = i
        debug("SelectPathDialog.layout", childs_length=len(self.childs))

    def make_focused_column_visible(self, align_to_right: bool):
        if (self.moved_to_make_tail_visible() if align_to_right else 0) + self.moved_to_make_head_visible() > 0:
            self.redraw()

    def moved_to_make_head_visible(self) -> int:
        x = self.focus_w.x
        if x < 0:
            self.x -= x
            self.layout()
            return 1
        return 0

    def moved_to_make_tail_visible(self) -> int:
        x_to = self.focus_w.x + self.focus_w.width
        if x_to > self.screen_width:
            self.x -= x_to - self.screen_width
            self.layout()
            return 1
        return 0

    def handle_mouse(self, x, y):
        pass

    def handle_key(self, key):
        if key == KEY_QUIT:
            return KEY_QUIT
        if key == KEY_ESC and self.finish_on_esc:
            return ACTION_CANCEL
        if key == KEY_ALT_HOME:
            self.focus_idx = -1
            return KEY_ALT_HOME
        if key != KEY_ENTER and key != KEY_SHIFT_TAB and key != KEY_TAB and key in KEYS_TO_EXIT_CODES:
            return key

        if key == KEY_RIGHT:
            debug("handle_key", key="KEY_RIGHT", focus_idx=self.focus_idx)
            # self.folder_lists.search()
            self.layout()
            if self.focus_idx == len(self.folder_lists.boxes) - 1:
                if self.folder_lists.try_to_go_in(self.focus_idx):
                    debug("handle_key", key="KEY_RIGHT", ok=True, boxes_length=len(self.folder_lists.boxes))
                    self.layout()
                    self.redraw()
                    self.move_focus(1)
            else:
                self.move_focus(1)

            self.make_focused_column_visible(True)
            self.folder_lists.boxes[self.focus_idx].make_cur_line_visible()
            self.redraw()
        elif key == KEY_LEFT:
            # self.folder_lists.search()
            self.layout()
            if self.focus_idx != 0:
                self.move_focus(-1)
            self.make_focused_column_visible(False)
            self.folder_lists.boxes[self.focus_idx].make_cur_line_visible()
            self.redraw()
        elif key == KEY_HOME:
            # self.folder_lists.search()
            self.layout()
            self.focus_idx = 0
            self.change_focus(self.folder_lists.boxes[self.focus_idx])
            self.make_focused_column_visible(False)
            self.folder_lists.boxes[self.focus_idx].make_cur_line_visible()
            self.redraw()
        elif key == KEY_END:
            # self.folder_lists.search()
            self.layout()
            self.focus_idx = self.folder_lists.index_of_last_list()
            self.change_focus(self.folder_lists.boxes[self.focus_idx])
            self.make_focused_column_visible(True)
            self.folder_lists.boxes[self.focus_idx].make_cur_line_visible()
            self.redraw()
        elif self.focus_w:
            if key == KEY_SHIFT_TAB:
                self.focus_idx = -1
                return ACTION_OK
            if key == KEY_TAB:
                self.focus_idx = self.folder_lists.index_of_last_list()
            if key == KEY_ENTER or key == KEY_TAB:
                for i in range(0, self.focus_idx + 1):
                    self.folder_lists.memorize_choice_in_list(i, True)
                return ACTION_OK

            # choice_before = self.focus_w.cur_line
            if self.handle_search_key(key):
                # self.redraw()
                res = True
            else:
                if key == KEY_UP or key == KEY_DOWN or key == KEY_PGUP or key == KEY_PGDN:
                    self.folder_lists.search()

                res = self.focus_w.handle_key(key)
            # choice_after = self.focus_w.cur_line

            # if choice_before != choice_after:
            if True:
                self.folder_lists.activate_sibling(self.focus_idx)
                self.layout()
                self.redraw()

            # if res == ACTION_PREV:
            #     self.move_focus(-1)
            # elif res == ACTION_NEXT:
            #     self.move_focus(1)
            # else:
            #     return res
            return res

    def items_path(self):
        return self.folder_lists.items_path(self.focus_idx)

    def handle_search_key(self, key):
        debug("handle_search_key", key=key)
        widget: WListBox = self.focus_w

        if key == KEY_DELETE:
            self.folder_lists.search_string = ''
            self.folder_lists.match_string = ''
            # self.search_widget_all(widget)
        elif key == KEY_ALT_UP:
            self.search_widget_up(widget)
        elif key == KEY_ALT_DOWN:
            self.search_widget_down(widget)
        elif key == KEY_ALT_PAGE_UP:
            self.search_widget_first(widget)
        elif key == KEY_ALT_PAGE_DOWN:
            self.search_widget_last(widget)
        elif key == KEY_ALT_RIGHT:
            res = self.search_widgets_right()
            if res is not None:
                self.change_focus(self.folder_lists.boxes[self.focus_idx])
                self.make_focused_column_visible(True)
            return True
        elif key == KEY_ALT_LEFT:
            res = self.search_widgets_left()
            if res is not None:
                self.change_focus(self.folder_lists.boxes[self.focus_idx])
                self.make_focused_column_visible(True)
            return True
        elif key == KEY_BACKSPACE:
            new_search_string = self.folder_lists.search_string[:-1]
            self.folder_lists.search(new_search_string)
            # self.search_widget_all(widget)
        elif type(key) is bytes and not key.startswith(b'\x1b'):
            debug('SelectPathDialog.handle_search_key', key=key)
            self.folder_lists.search(self.folder_lists.search_string + key.decode("utf-8"))
            count, idx, line, match_indices_by_box = self.matches_in_boxes()
            debug('SelectPathDialog.handle_search_key', count=count)
            if count == 1:
                # Just 1 match in all widgets
                self.focus_idx = idx
                box = self.folder_lists.boxes[idx]
                box.cur_line = line
                box.make_cur_line_visible()
                self.change_focus(box)
                self.make_focused_column_visible(True)
                # self.folder_lists.search()
            elif self.focus_idx in match_indices_by_box:
                # Do not search in the current box.
                # It will change selection, and matches in other boxes will be 'lost'.
                # And the user, perhaps, searched for them.
                # Disappearing matches are frustrating.

                # -- better to binary-search for nearest match?
                box = self.folder_lists.boxes[self.focus_idx]
                # box.cur_line = match_indices_by_box[self.focus_idx][0]
                box.make_cur_line_visible()
            else:
                debug('SelectPathDialog.handle_search_key', focused=False)
            return True
        else:
            return False

        return True

    def search_widget_last(self, widget):
        self.search_widget_and_scroll(range(len(widget.items) - 1, widget.cur_line, -1), False, widget)

    def search_widget_first(self, widget):
        self.search_widget_and_scroll(range(0, len(widget.items)), False, widget)

    def search_widget_down(self, widget):
        self.search_widget_and_scroll(range(widget.cur_line + 1, len(widget.items)), False, widget)

    def search_widget_up(self, widget):
        self.search_widget_and_scroll(range(widget.cur_line - 1, -1, -1), False, widget)

    def search_widget_all(self, widget: WListBox, skip_if_on_match=True):
        return self.search_widget_and_scroll(range(widget.cur_line, widget.cur_line + len(widget.items)), skip_if_on_match, widget)

    def search_widget_and_scroll(self, search_range, skip_if_on_match, widget: CustomListBox):
        if self.folder_lists.match_string != '':
            if skip_if_on_match and list_item_info_service.item_file_name(widget.items[widget.cur_line]).find(self.folder_lists.match_string) != -1:
                return
            for j in search_range:
                i = j % len(widget.items)
                if list_item_info_service.item_file_name(widget.items[i]).find(self.folder_lists.match_string) != -1:
                    widget.cur_line = widget.choice = i
                    widget.make_cur_line_visible()
                    return i

    def search_widget_get_matches(self, widget: WListBox) -> Tuple[int, int, List[int]]:
        match_count = 0
        last_match_line = 0
        match_indices = []
        if self.folder_lists.match_string != '':
            for i in range(0, len(widget.items)):
                if list_item_info_service.item_file_name(widget.items[i]).find(self.folder_lists.match_string) != -1:
                    match_count += 1
                    last_match_line = i
                    match_indices.append(i)
        return match_count, last_match_line, match_indices

    def matches_in_boxes(self) -> Tuple[int, int, int, Dict[int, List[int]]]:
        count = 0
        last_line = 0
        last_idx = 0
        match_indices_by_widget = {}
        for idx in range(0, len(self.folder_lists.boxes)):
            matches_in_widget, last_match_line, match_indices = self.search_widget_get_matches(self.folder_lists.boxes[idx])
            if matches_in_widget > 0:
                count += matches_in_widget
                last_idx = idx
                last_line = last_match_line
                match_indices_by_widget[idx] = match_indices
        return count, last_idx, last_line, match_indices_by_widget

    def search_widgets_right(self) -> Optional[int]:
        return self.search_widgets(range(self.focus_idx + 1, len(self.folder_lists.boxes)))

    def search_widgets_left(self) -> Optional[int]:
        return self.search_widgets(range(self.focus_idx - 1, -1, -1))

    def search_widgets(self, search_range, focus=True) -> Optional[int]:
        for i in search_range:
            box = self.folder_lists.boxes[i]
            res = self.search_widget_all(box, skip_if_on_match=False)
            if res is not None and focus:
                self.focus_idx = i
                return res
        return None
