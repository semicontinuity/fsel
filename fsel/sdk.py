import json
from stat import S_ISVTX, S_ISGID
from typing import Optional, List, Dict, AnyStr, Tuple, Callable, Iterable, Sequence, Set

from picotui.widgets import WListBox, Dialog, ACTION_CANCEL, ACTION_OK

from .exit_codes import EXIT_CODE_ENTER, EXIT_CODE_ESCAPE
from .exit_codes_mapping import KEYS_TO_EXIT_CODES
from .picotui_patch import patch_picotui

patch_picotui()
from fsel.picotui_patch import *

from picotui.defs import *
import os
import sys

screen = Screen()

KEY_ALT_UP = b'\x1b[1;3A'
KEY_ALT_DOWN = b'\x1b[1;3B'
KEY_ALT_PAGE_UP = b'\x1b[5;3~'
KEY_ALT_PAGE_DOWN = b'\x1b[6;3~'

KEY_ALT_RIGHT = b'\x1b[1;3C'
KEY_ALT_LEFT = b'\x1b[1;3D'
KEY_CTRL_RIGHT = b'\x1b[1;5C'
KEY_CTRL_LEFT = b'\x1b[1;5D'

KEY_CTRL_HOME = b'\x1b[1;5H'
KEY_CTRL_END = b'\x1b[1;5F'


class PaintContext:
    cur_x: int = sys.maxsize
    cur_y: int = sys.maxsize
    min_x: int = 0
    min_y: int = 0
    max_x: int = 0
    max_y: int = 0

    def goto(self, x: int, y: int):
        self.cur_x = x
        self.cur_y = y
        if self.min_x <= x < self.max_x and self.min_y <= y < self.max_y:
            Screen.goto(x, y)

    def paint_string(self, s: str):
        x = self.cur_x
        length = len(s)
        new_x = x + length

        if self.min_y <= self.cur_y < self.max_y:
            before = max(0, self.min_x - self.cur_x)
            after = max(0, new_x - self.max_x)
            to = length - after
            if to > before:
                if before > 0:
                    Screen.goto(self.min_x, self.cur_y)
                Screen.wr(s[before:to])
            if to == before:
                Screen.goto(new_x, self.cur_y)

        self.cur_x = new_x

    def clear_num_pos(self, length: int):
        x = self.cur_x
        new_x = x + length

        if self.min_y <= self.cur_y < self.max_y:
            before = max(0, self.min_x - self.cur_x)
            after = max(0, new_x - self.max_x)
            to = length - after
            if to > before:
                if before > 0:
                    Screen.goto(self.min_x, self.cur_y)
                Screen.wr("\x1b[%dX" % (to - before))
            if to == before:
                Screen.goto(new_x, self.cur_y)

        self.cur_x = new_x

    def clear_box(self, left, top, width, height):
        # "\x1b[%s;%s;%s;%s$z" doesn't work
        s = b" " * width
        bottom = top + height
        while top < bottom:
            self.goto(left, top)
            self.clear_num_pos(width)
            top += 1


p_ctx = PaintContext()


class FsListFiles:
    def __init__(self, root: AnyStr, select_files: bool, executables: bool, dot_files):
        self.root = root
        self.select_files = select_files
        self.executables = executables
        self.dot_files = dot_files

    def __call__(self, p: Sequence[str]) -> Sequence[Tuple[str, int]]:
        """ Each item is a tuple; last element of tuple is int with item attributes (same as in st_mode) """
        return self.list_folders(p) + self.list_files(p)

    def list_folders(self, path: Sequence[str]) -> List[Tuple[str, int]]:
        full_fs_path = os.path.join(self.root, *path)
        try:
            result = []
            for entry in os.scandir(full_fs_path):
                if entry.is_dir() and not entry.name.startswith('.'):
                    result.append((entry.name, entry.stat().st_mode | ItemModel.FLAG_DIRECTORY))
            return sorted(result, key=lambda e: e[0])
        except PermissionError:
            return []

    def list_files(self, p: Sequence[str]) -> List[Tuple[str, int]]:
        if not self.select_files:
            return []
        full_fs_path = os.path.join(self.root, *p)
        try:
            name: List[str] = os.listdir(full_fs_path)
            return [(entry, 0) for entry in sorted(name) if self.is_suitable_file(full_fs_path, entry)]
        except PermissionError:
            return []

    def is_suitable_file(self, folder, name):
        return (self.dot_files or not name.startswith('.')) and self.is_suitable_file_path(folder + '/' + name)

    def is_suitable_file_path(self, path):
        is_file = os.path.isfile(path)
        if not is_file: return False
        if self.executables: return os.access(path, os.X_OK)
        return True


class Oracle:
    def memorize(self, path: Sequence[AnyStr], name: AnyStr, persistent: bool):
        pass

    def recall_chosen_name(self, path: Sequence[AnyStr]) -> Optional[AnyStr]:
        pass

    def recall_choice(self, path: Sequence[AnyStr], items) -> int:
        pass


class PathOracle(Oracle):
    def __init__(self, root_history: Dict):
        self.root_history = root_history
        self.visit_history = {}

    def memorize(self, path: Sequence[AnyStr], name: AnyStr, persistent: bool):
        history = self.root_history if persistent else self.visit_history
        history[self.string_path(path)] = name

    def recall_chosen_name(self, path: Sequence[AnyStr]) -> Optional[AnyStr]:
        string_path = self.string_path(path)
        return self.visit_history.get(string_path) or self.root_history.get(string_path)

    @staticmethod
    def string_path(path: Sequence):
        return '/'.join(path)


class JsonModel:
    def __init__(self, data):
        self.data = data

    def list_items(self, path: List[AnyStr]):
        return self.list_items_of(self.data, path)

    def list_items_of(self, j, path: List[AnyStr]):
        if not path:
            if isinstance(j, dict):
                return [[k, False] for k in j.keys()]
            elif isinstance(j, list):
                return [[str(k), False] for k in range(len(j))]
            else:
                return []
        else:
            return self.list_items_of(self.resolve(j, path[0]), path[1:])

    def resolve(self, j, s: AnyStr):
        if isinstance(j, dict):
            return j[s]
        if isinstance(j, list):
            return j[int(s)]


class ItemModel:
    FLAG_DIRECTORY = 0x8000

    def attrs(self, item: Tuple[str, int]):
        return item[1]

    def is_leaf(self, item: Tuple[str, int]):
        return (item[1] & ItemModel.FLAG_DIRECTORY) == 0

    def max_item_text_length(self, items):
        return max(len(item[0]) for item in items)

    def item_text(self, item: Tuple[str, int]) -> str:
        return item[0]

    def index_of_item_text(self, text, items: Iterable[Tuple[str, int]]) -> Optional[int]:
        for i, item in enumerate(items):
            if text == self.item_text(item):
                return i


class CustomListBox(WListBox):
    def __init__(self, w, h, items: Sequence[Tuple[str, int]], folder=None, search_string_supplier=lambda: ''):
        super().__init__(w, h, items)
        self.folder = folder
        self.search_string_supplier = search_string_supplier
        self.all_items = items

    def __repr__(self):
        return f'{self.folder}: {self.items[self.cur_line]}'

    def make_cur_line_visible(self):
        overshoot = self.cur_line - (self.top_line + self.height)
        if overshoot > 0:
            self.top_line += overshoot + 1
        undershoot = self.top_line - self.cur_line
        if undershoot > 0:
            self.top_line -= undershoot
        self.top_line = max(self.top_line, 0)   # becomes negative when search-filtering?

    @staticmethod
    def goto(x, y):
        p_ctx.goto(x, y)

    def show_line(self, item, i):
        """ item: line value; i: -1 for off-limit lines """
        if i == -1:
            self.attr_reset()
            p_ctx.clear_num_pos(self.width)
            self.attr_reset()
        else:
            self.show_real_line(item, i)

    def show_real_line(self, item, i):
        search_string = self.search_string_supplier()
        l = item_model.item_text(item)
        match_from = -1 if len(search_string) <= 0 else l.find(search_string)
        match_to = match_from + len(search_string)
        l = l[:self.width]
        match_from = min(match_from, self.width)
        match_to = min(match_to, self.width)
        palette = colors.palette(item_model.attrs(item), self.focus, self.cur_line == i)

        if match_from != -1:
            self.attr_reset()
            self.attr_color(palette[Colors.C_IDX_REG_FG], palette[Colors.C_IDX_BG])

            p_ctx.paint_string(l[:match_from])

            self.attr_reset()
            self.attr_color(palette[Colors.C_IDX_MATCH_FG], palette[Colors.C_IDX_BG])
            p_ctx.paint_string(l[match_from: match_to])

            self.attr_reset()
            self.attr_color(palette[Colors.C_IDX_REG_FG], palette[Colors.C_IDX_BG])
            p_ctx.paint_string(l[match_to:])
        else:
            self.attr_reset()
            self.attr_color(palette[Colors.C_IDX_REG_FG], palette[Colors.C_IDX_BG])
            p_ctx.paint_string(l)

        p_ctx.clear_num_pos(self.width - len(l))
        self.attr_reset()

    def handle_cursor_keys(self, key):
        result = super().handle_cursor_keys(key)
        self.make_cur_line_visible()
        self.redraw()
        return result

    @staticmethod
    def attr_color(fg, bg=-1):
        Screen.wr("\x1b[38;5;%d;48;5;%dm" % (fg, bg))

    def search(self, s: str):
        content = []
        cur_item = self.items[self.cur_line]
        new_current_line = 0

        for i, item in enumerate(self.all_items):
            if item == cur_item or item_model.item_text(item).find(s) >= 0:
                if item == cur_item:
                    new_current_line = len(content)
                content.append(item)

        self.set_items(content)
        self.cur_line = new_current_line


class ListBoxes:
    boxes: List[CustomListBox]
    search_string: str = ''

    def __init__(self, entry_lister: Callable[[Sequence[str]], Sequence[Tuple[str, int]]], oracle: Oracle, initial_path: List):
        self.entry_lister = entry_lister
        self.oracle = oracle
        self.boxes = self.boxes_for_path(initial_path)
        self.expand_lists()

    def search(self, s: str = ''):
        self.search_string = s
        for child in self.boxes:
            child.search(s)

    def boxes_for_path(self, initial_path: Sequence[str]) -> List[CustomListBox]:
        lists = []
        index = 0
        while True:
            a_list = self.make_box_or_none(initial_path[:index])
            if a_list is None:
                break
            lists.append(a_list)
            index += 1
            if index > len(initial_path):
                break

        for index, l in enumerate(lists):
            if index == len(lists) - 1:
                l.focus = True
                break
            l.cur_line = l.choice = item_model.index_of_item_text(initial_path[index], l.items) or 0

        return lists

    def expand_lists(self):
        index = len(self.boxes) - 1
        while True:
            if self.is_at_leaf(index):
                break
            path = self.path(index)
            name = self.oracle.recall_chosen_name(path)
            index += 1
            a_list = self.make_box_or_none(path)
            if a_list is None or a_list.cur_line is None:
                break
            self.boxes.append(a_list)
            if len(a_list.items) == 1:
                continue
            if name is None:
                break

    def activate_sibling(self, index):
        self.boxes = self.boxes[: index + 1]
        self.expand_lists()
        self.memorize_choice_in_list(index, False)

    def try_to_go_in(self, index):
        if index != len(self.boxes) - 1 or self.is_at_leaf(index):
            return

        self.memorize_choice_in_list(index, False)

        new_box = self.make_box_or_none(self.path(index))
        if new_box is None:
            return

        self.boxes.append(new_box)
        self.expand_lists()
        return True

    def make_box_or_none(self, path: Sequence[str]) -> Optional[CustomListBox]:
        items = self.entry_lister(path)
        if len(items) == 0:
            return None
        return self.make_box(path, items)

    def make_box(self, path: Sequence[str], items: Sequence[Tuple[str, int]]):
        box = CustomListBox(item_model.max_item_text_length(items), len(items), items, path, lambda: self.search_string)
        last_name = self.oracle.recall_chosen_name(path)
        choice = item_model.index_of_item_text(last_name, items)
        box.cur_line = box.choice = 0 if choice is None else choice
        return box

    def memorize_choice_in_list(self, index, persistent: bool):
        parent_path = [] if index == 0 else self.path(index - 1)
        self.oracle.memorize(parent_path, item_model.item_text(self.selected_item_in_list(index)), persistent)

    def index_of_last_list(self):
        return len(self.boxes) - 1

    def is_at_leaf(self, index):
        return item_model.is_leaf(self.selected_item_in_list(index))

    def selected_item_in_list(self, index):
        return self.boxes[index].items[self.boxes[index].cur_line]

    def max_child_height(self):
        return max(len(child.items) for child in self.boxes)

    def is_empty(self):
        return len(self.boxes) == 0

    def path(self, index) -> List[str]:
        return [item_model.item_text(l.items[l.cur_line]) for l in self.boxes[: index + 1]]

    def items_path(self, index):
        return [l.items[l.cur_line] for l in self.boxes[: index + 1]]


class DynamicDialog(Dialog):
    def __init__(self, screen_height, x, y, w=0, h=0):
        super().__init__(x, y, w, h)
        self.screen_height = screen_height

    def request_height(self, max_child_h):
        old_h = self.h
        self.h = min(max_child_h, self.screen_height)
        if old_h > self.h:
            p_ctx.clear_box(self.x, self.y + self.h, self.w, old_h - self.h)

        overshoot = max(self.y + self.h - self.screen_height, 0)
        if overshoot > 0:
            Screen.goto(0, self.screen_height - 1)
            for _ in range(overshoot):
                Screen.wr('\r\n')
            self.y -= overshoot

    def redraw(self):
        # Init some state on first redraw
        if self.focus_idx == -1:
            self.autosize()
            self.focus_idx, self.focus_w = self.find_focusable_by_idx(0, 1)
            if self.focus_w:
                self.focus_w.focus = True

        self.clear()
        for w in self.childs:
            w.redraw()

    def clear(self):
        self.attr_reset()
        p_ctx.clear_box(self.x, self.y, self.w, self.h)


class AbstractSelectionDialog(DynamicDialog):
    def items_path(self) -> List:
        pass


class SelectPathDialog(AbstractSelectionDialog):
    def __init__(self, folder_lists: ListBoxes, screen_width, screen_height, width, height, x, y):
        super().__init__(screen_height, x, y, width, height)
        self.screen_width = screen_width
        self.folder_lists = folder_lists
        self.layout()
        self.make_focused_column_visible(True)

    def layout(self):
        self.request_height(self.folder_lists.max_child_height())
        self.childs = []
        child_x = 0

        for i, child in enumerate(self.folder_lists.boxes):
            child.h = child.height = min(len(child.items), self.h)
            self.add(child_x, 0, child)
            child_x += child.width + 1
            if child.focus:
                self.focus_w = child
                self.focus_idx = i

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

        if key in KEYS_TO_EXIT_CODES:
            return key

        if key == KEY_RIGHT:
            self.folder_lists.search()
            self.layout()
            if self.focus_idx == len(self.folder_lists.boxes) - 1:
                if self.folder_lists.try_to_go_in(self.focus_idx):
                    self.redraw()
                    self.move_focus(1)
            else:
                self.move_focus(1)

            self.make_focused_column_visible(True)
            self.folder_lists.boxes[self.focus_idx].make_cur_line_visible()
            self.redraw()
        elif key == KEY_LEFT:
            self.folder_lists.search()
            self.layout()
            if self.focus_idx != 0:
                self.move_focus(-1)
            self.make_focused_column_visible(False)
            self.folder_lists.boxes[self.focus_idx].make_cur_line_visible()
            self.redraw()
        elif key == KEY_HOME:
            self.folder_lists.search()
            self.layout()
            self.focus_idx = 0
            self.change_focus(self.folder_lists.boxes[self.focus_idx])
            self.make_focused_column_visible(False)
            self.folder_lists.boxes[self.focus_idx].make_cur_line_visible()
            self.redraw()
        elif key == KEY_END:
            self.folder_lists.search()
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
        widget: WListBox = self.focus_w

        if key == KEY_DELETE:
            self.folder_lists.search_string = ''
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
            self.folder_lists.search(self.folder_lists.search_string[:-1])
            # self.search_widget_all(widget)
        elif type(key) is bytes and not key.startswith(b'\x1b'):
            self.folder_lists.search(self.folder_lists.search_string + key.decode("utf-8"))
            count, idx, line, match_indices_by_widget = self.search_widgets_all()
            if count == 1:
                self.focus_idx = idx
                box = self.folder_lists.boxes[idx]
                box.cur_line = line
                box.make_cur_line_visible()
                self.change_focus(box)
                self.make_focused_column_visible(True)
                self.folder_lists.search()
            elif self.focus_idx in match_indices_by_widget:
                # better to binary-search for nearest match?
                box = self.folder_lists.boxes[self.focus_idx]
                box.cur_line = match_indices_by_widget[self.focus_idx][0]
                box.make_cur_line_visible()
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
        if self.folder_lists.search_string != '':
            if skip_if_on_match and item_model.item_text(widget.items[widget.cur_line]).find(self.folder_lists.search_string) != -1:
                return
            for j in search_range:
                i = j % len(widget.items)
                if item_model.item_text(widget.items[i]).find(self.folder_lists.search_string) != -1:
                    widget.cur_line = widget.choice = i
                    widget.make_cur_line_visible()
                    return i

    def search_widget_get_match(self, widget: WListBox) -> Tuple[int, int, List[int]]:
        match_count = 0
        last_match_line = 0
        match_indices = []
        if self.folder_lists.search_string != '':
            for i in range(0, len(widget.items)):
                if item_model.item_text(widget.items[i]).find(self.folder_lists.search_string) != -1:
                    match_count += 1
                    last_match_line = i
                    match_indices.append(i)
        return match_count, last_match_line, match_indices

    def search_widgets_all(self) -> Tuple[int, int, int, Dict[int, List[int]]]:
        count = 0
        last_line = 0
        last_idx = 0
        match_indices_by_widget = {}
        for idx in range(0, len(self.folder_lists.boxes)):
            matches_in_widget, last_match_line, match_indices = self.search_widget_get_match(self.folder_lists.boxes[idx])
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


class ItemSelectionDialog(AbstractSelectionDialog):
    def __init__(self, screen_height, width, height, x, y, items):
        super().__init__(screen_height, 0, 0, width, height)
        self.x = x
        self.y = y
        self.request_height(len(items))
        self.add(0, 0, CustomListBox(item_model.max_item_text_length(items), len(items), items))

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


class AllSettingsFolder:
    roots: Set[str] = set()

    def __init__(self, all_settings_folder: str):
        os.makedirs(all_settings_folder, exist_ok=True)
        self.all_settings_folder = all_settings_folder
        for entry in os.scandir(all_settings_folder):
            if entry.is_file():
                self.roots.add(entry.name.replace('\\', '/'))

    def load_settings(self, root: AnyStr):
        try:
            with open(self.settings_file(root)) as json_file:
                return json.load(json_file)
        except:
            return {}

    def save(self, settings, root: AnyStr):
        try:
            with open(self.settings_file(root), 'w') as f:
                json.dump(settings, f, indent=2, sort_keys=True)
        except:
            pass

    def settings_file(self, root):
        return self.all_settings_folder + '/' + root.replace('/', '\\')


class Colors:
    BLUE = 17
    B_YELLOW = 227
    B_GREEN = 120
    GRAY = 248
    CYAN = 31

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

    @staticmethod
    def palette(attrs: int, focused_list: bool, focused_entry: bool) -> List[int]:
        """ category: one of C_IDX_* constants """

        if (attrs & ItemModel.FLAG_DIRECTORY) and (attrs & S_ISVTX):
            palette = Colors.C_STICKY_FOLDER
        elif (attrs & ItemModel.FLAG_DIRECTORY) and (attrs & S_ISGID):
            palette = Colors.C_SGID_FOLDER
        elif attrs & ItemModel.FLAG_DIRECTORY:
            palette = Colors.C_FOLDER
        else:
            palette = Colors.C_LEAF

        return palette[2 * int(focused_list) + int(focused_entry)]


colors = Colors()
item_model = ItemModel()
