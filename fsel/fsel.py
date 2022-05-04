from typing import Optional, List, Dict, AnyStr, Tuple

from picotui.widgets import WListBox, Dialog, ACTION_CANCEL, ACTION_PREV, ACTION_NEXT, ACTION_OK

from .picotui_patch import patch_picotui

patch_picotui()
from fsel.picotui_patch import *

from picotui.defs import *
import os
import sys
import json

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

RECENT_COUNT = 10

C_IDX_BG = 0
C_IDX_REG_FG = 1
C_IDX_MATCH_FG = 2

C_FOLDER = [
    # non focused list; non highlighted entry
    [C_BLACK, C_B_WHITE, C_B_RED],
    # non focused list; highlighted entry
    [C_BLUE, C_B_WHITE, C_B_RED],
    # focused list; non highlighted entry
    [C_BLACK, C_B_WHITE, C_B_RED],
    # focused list; highlighted entry
    [C_CYAN, C_B_WHITE, C_B_RED]
]

C_LEAF = [
    # non focused list; non highlighted entry
    [C_BLACK, C_BLUE, C_B_YELLOW],
    # non focused list; highlighted entry
    [C_GREEN, C_BLACK, C_B_YELLOW],
    # focused list; non highlighted entry
    [C_BLACK, C_BLUE, C_B_YELLOW],
    # focused list; highlighted entry
    [C_CYAN, C_WHITE, C_B_YELLOW]
]


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


class FsModel:
    def __init__(self, root: AnyStr, show_files: bool, executables: bool, root_history):
        self.root = root
        self.select_files = show_files
        self.executables = executables
        self.root_history = root_history
        self.visit_history = {}

    def list_items(self, path: List) -> List:
        full_fs_path = os.path.join(self.root, *path)
        try:
            entries: List[str] = os.listdir(full_fs_path)
            items = [(name, False) for name in sorted(entries) if
                             os.path.isdir(full_fs_path + '/' + name) and not name.startswith('.')]
            if self.select_files:
                items += [
                    (name, True) for name in sorted(entries)
                    if self.is_suitable_file(full_fs_path, name)
                ]
            return items

        except PermissionError:
            return []

    def is_suitable_file(self, folder, name):
        path = folder + '/' + name
        return not name.startswith('.') and self.is_suitable_file_path(path)

    def is_suitable_file_path(self, path):
        return os.path.isfile(path) and os.access(path, os.X_OK) == self.executables

    def full_path(self, items_path):
        path = os.path.join(self.root, *[model.item_text(i) for i in items_path])
        if self.select_files:
            return path if self.is_suitable_file_path(path) else None
        else:
            return path

    def memorize(self, path: List[AnyStr], name: AnyStr, persistent: bool):
        storage = self.root_history if persistent else self.visit_history
        storage[self.string_path(path)] = name

    def recall_chosen_name(self, path):
        string_path = self.string_path(path)
        return self.visit_history.get(string_path) or \
               self.root_history.get(string_path)

    def recall_choice(self, path, items):
        string_path = self.string_path(path)
        return FsModel.recall_choice_in(self.visit_history, string_path, items) or \
               FsModel.recall_choice_in(self.root_history, string_path, items)

    @staticmethod
    def recall_choice_in(storage, path, items):
        if path in storage:
            last_name = storage[path]
            if last_name is not None:
                return model.index_of_item_text(last_name, items)

    def string_path(self, path):
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


class Model:
    def is_leaf(self, item):
        return item[1]

    def max_item_text_length(self, items):
        return max(len(item[0]) for item in items)

    def item_text(self, item):
        return item[0]

    def index_of_item_text(self, text, items):
        for i, item in enumerate(items):
            if text == item[0]:
                return i


model = Model()


class CustomListBox(WListBox):
    def __init__(self, w, h, items, folder=None, search_string_supplier=lambda: ''):
        super().__init__(w, h, items)
        self.folder = folder
        self.search_string_supplier = search_string_supplier

    def __repr__(self):
        return f'{self.folder}: {self.items[self.cur_line]}'

    def make_cur_line_visible(self):
        overshoot = self.cur_line - (self.top_line + self.height)
        if overshoot > 0:
            self.top_line += overshoot + 1
        undershoot = self.top_line - self.cur_line
        if undershoot > 0:
            self.top_line -= undershoot

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
        is_leaf = model.is_leaf(item)
        l = model.item_text(item)
        match_from = -1 if len(search_string) <= 0 else l.find(search_string)
        match_to = match_from + len(search_string)
        l = l[:self.width]
        match_from = min(match_from, self.width)
        match_to = min(match_to, self.width)

        palette = (C_LEAF if is_leaf else C_FOLDER)[2 * int(self.focus) + int(self.cur_line == i)]

        if match_from != -1:
            self.attr_reset()
            self.attr_color(palette[C_IDX_REG_FG], palette[C_IDX_BG])
            p_ctx.paint_string(l[:match_from])

            self.attr_reset()
            self.attr_color(palette[C_IDX_MATCH_FG], palette[C_IDX_BG])
            p_ctx.paint_string(l[match_from: match_to])

            self.attr_reset()
            self.attr_color(palette[C_IDX_REG_FG], palette[C_IDX_BG])
            p_ctx.paint_string(l[match_to:])
        else:
            self.attr_reset()
            self.attr_color(palette[C_IDX_REG_FG], palette[C_IDX_BG])
            p_ctx.paint_string(l)

        p_ctx.clear_num_pos(self.width - len(l))
        self.attr_reset()


class ListBoxes:
    boxes: List[CustomListBox]
    search_string: str = ''

    def __init__(self, tree_model, initial_path):
        self.tree_model = tree_model
        self.boxes = self.boxes_for_path(initial_path)
        self.expand_lists()

    def boxes_for_path(self, initial_path) -> List[CustomListBox]:
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
            l.cur_line = l.choice = model.index_of_item_text(initial_path[index], l.items) or 0

        return lists

    def expand_lists(self):
        index = len(self.boxes) - 1
        while True:
            if self.is_at_leaf(index):
                break
            path = self.path(index)
            name = self.tree_model.recall_chosen_name(path)
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

    def make_box_or_none(self, path: List) -> Optional[CustomListBox]:
        items = self.tree_model.list_items(path)
        if len(items) == 0:
            return None
        return self.make_box(path, items)

    def make_box(self, path, items):
        box = CustomListBox(model.max_item_text_length(items), len(items), items, path, lambda: self.search_string)
        choice = self.tree_model.recall_choice(path, items)
        box.cur_line = box.choice = 0 if choice is None else choice
        return box

    def memorize_choice_in_list(self, index, persistent: bool):
        parent_path = [] if index == 0 else self.path(index - 1)
        self.tree_model.memorize(parent_path, model.item_text(self.selected_item_in_list(index)), persistent)

    def index_of_last_list(self):
        return len(self.boxes) - 1

    def is_at_leaf(self, index):
        return model.is_leaf(self.selected_item_in_list(index))

    def selected_item_in_list(self, index):
        return self.boxes[index].items[self.boxes[index].cur_line]

    def max_child_height(self):
        return max(len(child.items) for child in self.boxes)

    def is_empty(self):
        return len(self.boxes) == 0

    def path(self, index):
        return [model.item_text(l.items[l.cur_line]) for l in self.boxes[: index + 1]]

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


class SelectPathDialog(DynamicDialog):
    def __init__(self, folder_lists: ListBoxes, screen_width, screen_height, width, height, x, y):
        super().__init__(screen_height, x, y, width, height)
        self.screen_width = screen_width
        self.folder_lists = folder_lists
        self.layout()

    def layout(self):
        self.request_height(self.folder_lists.max_child_height())
        self.childs = []
        child_x = 0

        for i, child in enumerate(self.folder_lists.boxes):
            child.h = child.height = min(child.height, self.h)
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
        if key == KEY_RIGHT:
            self.folder_lists.search_string = ''
            self.redraw()

            if self.focus_idx == len(self.folder_lists.boxes) - 1:
                if self.folder_lists.try_to_go_in(self.focus_idx):
                    self.layout()
                    self.redraw()
                    self.move_focus(1)
            else:
                self.move_focus(1)

            self.make_focused_column_visible(True)
        elif key == KEY_LEFT:
            self.folder_lists.search_string = ''
            self.redraw()

            if self.focus_idx != 0:
                self.move_focus(-1)
            self.make_focused_column_visible(False)
        elif key == KEY_HOME:
            self.folder_lists.search_string = ''
            self.redraw()

            self.focus_idx = 0
            self.change_focus(self.folder_lists.boxes[self.focus_idx])
            self.make_focused_column_visible(False)
        elif key == KEY_END:
            self.folder_lists.search_string = ''
            self.redraw()

            self.focus_idx = self.folder_lists.index_of_last_list()
            self.change_focus(self.folder_lists.boxes[self.focus_idx])
            self.make_focused_column_visible(True)
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
            self.folder_lists.search_string = self.folder_lists.search_string[:-1]
            # self.search_widget_all(widget)
        elif type(key) is bytes and not key.startswith(b'\x1b'):
            self.folder_lists.search_string += key.decode("utf-8")
            count, idx, line = self.search_widgets_all()
            if count == 1:
                self.focus_idx = idx
                box = self.folder_lists.boxes[idx]
                box.cur_line = line
                box.make_cur_line_visible()
                self.change_focus(box)
                self.make_focused_column_visible(True)
                self.folder_lists.search_string = ''
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
            if skip_if_on_match and model.item_text(widget.items[widget.cur_line]).find(self.folder_lists.search_string) != -1:
                return
            for j in search_range:
                i = j % len(widget.items)
                if model.item_text(widget.items[i]).find(self.folder_lists.search_string) != -1:
                    widget.cur_line = widget.choice = i
                    widget.make_cur_line_visible()
                    return i

    def search_widget_get_match(self, widget: WListBox) -> Tuple[int, int]:
        count = 0
        line = 0
        if self.folder_lists.search_string != '':
            for i in range(0, len(widget.items)):
                if model.item_text(widget.items[i]).find(self.folder_lists.search_string) != -1:
                    count += 1
                    line = i
        return count, line

    def search_widgets_all(self) -> Tuple[int, int, int]:
        count = 0
        last_line = 0
        last_idx = 0
        for idx in range(0, len(self.folder_lists.boxes)):
            cnt, line = self.search_widget_get_match(self.folder_lists.boxes[idx])
            if cnt > 0:
                count += cnt
                last_idx = idx
                last_line = line
        return count, last_idx, last_line

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


class ItemSelectionDialog(DynamicDialog):
    def __init__(self, screen_height, width, height, x, y, items):
        super().__init__(screen_height, 0, 0, width, height)
        self.x = x
        self.y = y
        self.request_height(len(items))
        self.add(0, 0, CustomListBox(model.max_item_text_length(items), len(items), items))

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


def run(dialog_supplier):
    v = None
    try:
        Screen.init_tty()
        Screen.cursor(False)

        screen_width, screen_height = Screen.screen_size()
        cursor_y, cursor_x = cursor_position()
        p_ctx.max_x = screen_width
        p_ctx.max_y = screen_height

        v = dialog_supplier(screen_height, screen_width, cursor_y, cursor_x)
        if v.loop() == ACTION_OK:
            return v.items_path()
        else:
            return None
    finally:
        Screen.attr_reset()
        if v is not None:
            v.clear()
            Screen.goto(0, v.y)

        Screen.cursor(True)
        Screen.deinit_tty()


def full_path(root, rel_path):
    root = root + '/' if root != '/' else '/'
    return root + rel_path


def load_settings():
    try:
        with open(settings_file()) as json_file:
            return json.load(json_file)
    except:
        return {}


def save_settings(settings):
    try:
        with open(settings_file(), 'w') as f:
            json.dump(settings, f, indent=2, sort_keys=True)
    except Exception as e:
        pass


def settings_file():
    return os.getenv("HOME") + "/.fsel_history"


def find_root_for(folder, roots):
    path = folder if not folder.endswith('/') else folder[:len(folder) - 1]

    while True:
        if path in roots:
            return False, str(path)
        if path == os.getenv('HOME') or path == '' or path.startswith('.'):
            return False, path

        contents = os.listdir(path)
        if '.svn' in contents or '.git' in contents:
            return True, path

        i = path.rfind('/')
        path = path[:i]


def field_or_else(d: Dict, name, default):
    result = d.get(name)
    if result is None:
        d[name] = result = default
    return result


def file_ops(folder):
    target_is_file = '-f' in sys.argv[1:]
    target_is_executable = '-x' in sys.argv[1:]

    settings = load_settings()
    vcs_root_detected, root = find_root_for(folder, settings)
    if vcs_root_detected:
        settings[root] = {}
    settings_for_root = field_or_else(settings, root, {})
    recent = field_or_else(settings_for_root, field_for_recent(target_is_file, target_is_executable), [])

    if '-e' in sys.argv[1:]:
        if len(recent) == 0:
            sys.exit(2)

        # makes little sense to cd to the current directory...
        if recent[0] == os.path.relpath(os.environ["PWD"], root) and len(recent) > 1:   # PWD for logical path
            recent[0], recent[1] = recent[1], recent[0]

        recent_items = [(name, False) for name in recent]
        items_path = run(
            lambda screen_height, screen_width, cursor_y, cursor_x:
            ItemSelectionDialog(screen_height, screen_width, 0, 0, cursor_y, recent_items)
        )
        if items_path is None:
            sys.exit(1)
        path = full_path(root, model.item_text(items_path[0]))
        if path is None:
            sys.exit(1)
    else:
        root_history = field_or_else(settings_for_root, 'history', {})
        fs_model = FsModel(root, target_is_file, target_is_executable, root_history)

        rel_path = os.path.relpath(folder, root)
        initial_path = rel_path.split('/') if rel_path != '.' else []
        folder_lists = ListBoxes(fs_model, initial_path)
        if folder_lists.is_empty():
            sys.exit(2)

        items_path = run(
            lambda screen_height, screen_width, cursor_y, cursor_x:
            SelectPathDialog(folder_lists, screen_width, screen_height, width=1000, height=0, x=0, y=cursor_y)
        )
        if items_path is None:
            sys.exit(1)
        path = fs_model.full_path(items_path)
        if path is None:
            sys.exit(1)

    rel_path_from_root = os.path.relpath(path, start=root)
    update_recents(recent, rel_path_from_root)
    save_settings(settings)

    print(to_requested_kind(path, rel_path_from_root))


def field_for_recent(target_is_file, target_is_executable):
    if target_is_file:
        return 'recent-executables' if target_is_executable else 'recent-files'
    else:
        return 'recent-folders'


def update_recents(recent, rel_path_from_root):
    if rel_path_from_root != '.':
        if rel_path_from_root in recent:
            recent.remove(rel_path_from_root)
        recent.insert(0, rel_path_from_root)
        del recent[RECENT_COUNT:]


def to_requested_kind(path, rel_path_from_root):
    ret_rel_path = '-r' in sys.argv[1:]
    ret_rel_path_from_root = '-R' in sys.argv[1:]
    if ret_rel_path:
        return os.path.relpath(path)
    elif ret_rel_path_from_root:
        return rel_path_from_root
    else:
        return path


if __name__ == "__main__":
    if sys.stdin.isatty():
        path_args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
        file_ops(os.getenv('PWD') if len(path_args) != 1 else path_args[0])
