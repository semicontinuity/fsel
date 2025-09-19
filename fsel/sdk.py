from typing import Optional, List, Dict, AnyStr, Callable, Sequence

from datatools.tui.buffer.abstract_buffer_writer import AbstractBufferWriter
from picotui.widgets import WListBox, Dialog, ACTION_CANCEL, ACTION_OK

from fsel.list_item import ListItem
from fsel.rich_text import Style, RichText, render_substr
from .colors import Colors
from .exit_codes import EXIT_CODE_ENTER, EXIT_CODE_ESCAPE
from .exit_codes_mapping import KEYS_TO_EXIT_CODES
from .item_model import item_model
from .logging import debug
from fsel.lib.paint_context import PaintContext
from .palette import palette
from .picotui_patch import patch_picotui

patch_picotui()
from fsel.picotui_patch import *

from fsel.lib.ansi import attr_italic, attr_strike_thru, attr_reversed, attr_crossed_out, attr_not_crossed_out, \
    attr_not_reversed, attr_color

screen = Screen()
p_ctx = PaintContext()


class Oracle:
    def memorize(self, path: List[AnyStr], name: AnyStr, persistent: bool):
        pass

    def recall_chosen_name(self, path: List[AnyStr]) -> Optional[AnyStr]:
        pass

    def recall_choice(self, path: Sequence[AnyStr], items) -> int:
        pass


class CustomListBox(WListBox):
    def __init__(self, w, h, items: Sequence[ListItem], folder=None, search_string_supplier=lambda: '', is_full_match_supplier=lambda: True):
        super().__init__(w, h, items)
        self.folder = folder
        self.match_string_supplier = search_string_supplier
        self.is_full_match_supplier = is_full_match_supplier
        self.all_items = items

    def __repr__(self):
        return f'{self.folder}: {self.items[self.cur_line]} [focused:{self.focus}]'

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

    def show_line(self, item: ListItem, i: int):
        """ item: line value; i: -1 for off-limit lines """
        if i == -1:
            self.attr_reset()
            p_ctx.clear_num_pos(self.width)
            self.attr_reset()
        else:
            self.show_real_line(item, i)

    def show_real_line(self, item: ListItem, i):
        match_string = self.match_string_supplier()
        l = item_model.item_text(item)
        match_from = -1 if len(match_string) <= 0 else l.find(match_string)
        display_to = match_from + len(match_string)
        l = l[:self.width]
        display_from = min(match_from, self.width)
        display_to = min(display_to, self.width)
        debug('show_real_line', width=self.width, l=l, display_from=display_from, display_to=display_to)
        _palette = palette(item_model.attrs(item), self.focus, self.cur_line == i)

        if display_from != -1:
            self.attr_reset()
            attr_italic(item_model.is_italic(item))
            attr_strike_thru(item_model.is_strike_thru(item))
            attr_color(fg=_palette[Colors.C_IDX_REG_FG], bg=_palette[Colors.C_IDX_BG])

            p_ctx.paint_string(l[:display_from])

            attr_reversed()
            if not self.is_full_match_supplier():
                attr_crossed_out()
            p_ctx.paint_string(l[display_from: display_to])
            if not self.is_full_match_supplier():
                attr_not_crossed_out()
            attr_not_reversed()

            attr_color(_palette[Colors.C_IDX_REG_FG], _palette[Colors.C_IDX_BG])
            p_ctx.paint_string(l[display_to:])
        else:
            self.attr_reset()
            attr_italic(item_model.is_italic(item))
            attr_strike_thru(item_model.is_strike_thru(item))
            attr_color(_palette[Colors.C_IDX_REG_FG], _palette[Colors.C_IDX_BG])
            p_ctx.paint_string(l)

        p_ctx.clear_num_pos(self.width - len(l))
        self.attr_reset()
        
    def show_real_line2(self, item: ListItem, i):
        """Alternative implementation of show_real_line using RichText and render_substr"""
        match_string = self.match_string_supplier()
        l = item_model.item_text(item)
        match_from = -1 if len(match_string) <= 0 else l.find(match_string)
        display_to = match_from + len(match_string)
        l = l[:self.width]
        display_from = min(match_from, self.width)
        display_to = min(display_to, self.width)
        debug('show_real_line2', width=self.width, l=l, display_from=display_from, display_to=display_to)
        _palette = palette(item_model.attrs(item), self.focus, self.cur_line == i)
        
        # Create base style for regular text
        base_attr = 0
        if item_model.is_italic(item):
            base_attr |= AbstractBufferWriter.MASK_ITALIC

        base_style = Style(
            attr=base_attr,
            fg=_palette[Colors.C_IDX_REG_FG],
            bg=_palette[Colors.C_IDX_BG]
        )
        
        # Create style for matched text
        match_attr = base_attr
        if not self.is_full_match_supplier():
            match_attr |= AbstractBufferWriter.MASK_CROSSED_OUT
            
        match_style = Style(
            attr=match_attr,
            fg=_palette[Colors.C_IDX_REG_FG],
            bg=_palette[Colors.C_IDX_BG]
        )
        
        # Construct RichText object
        rich_text: RichText = []
        
        if display_from != -1:
            # Text before match
            if display_from > 0:
                rich_text.append((l[:display_from], base_style))
                
            # Matched text
            rich_text.append((l[display_from:display_to], match_style))
            
            # Text after match
            if display_to < len(l):
                rich_text.append((l[display_to:], base_style))
        else:
            # No match, just regular text
            rich_text.append((l, base_style))
        
        # Render the RichText
        result = render_substr(rich_text, 0, len(l))
        p_ctx.paint_string(result)
        
        p_ctx.clear_num_pos(self.width - len(l))
        self.attr_reset()

    def handle_cursor_keys(self, key):
        result = super().handle_cursor_keys(key)
        self.make_cur_line_visible()
        self.redraw()
        return result

    def search(self, s: str):
        content = []
        cur_item = self.items[self.cur_line]
        new_current_line = 0
        found = False

        for i, item in enumerate(self.all_items):
            debug('CustomListBox.search', s=s, i=i, item_file_name=item_model.item_file_name(item))
            is_current = item == cur_item
            is_match = item_model.item_file_name(item).find(s) >= 0
            if is_match:
                debug('CustomListBox.search', found=True)
                found = True
            if is_current:
                debug('CustomListBox.search', cur_line=self.cur_line)
                new_current_line = len(content)
            if is_match or is_current:
                content.append(item)

        return found, new_current_line, content


class ListBoxes:
    entry_lister: Callable[[Sequence[str]], Sequence[ListItem]]
    boxes: List[CustomListBox]
    search_string: str = ''
    match_string: str = ''

    def __init__(self, entry_lister: Callable[[Sequence[str]], Sequence[ListItem]], oracle: Oracle, initial_path: List):
        debug('ListBoxes', initial_path=initial_path)
        self.entry_lister = entry_lister
        self.oracle = oracle
        self.boxes = self.boxes_for_path(initial_path)
        debug('ListBoxes', boxes=self.boxes)

    def search(self, s: str = ''):
        debug('ListBoxes.search', s=s)
        self.search_string = s

        found_somewhere = False
        for box in self.boxes:
            found, new_current_line, content = box.search(s)
            found_somewhere |= found
        debug('ListBoxes.search', found_somewhere=found_somewhere)

        if found_somewhere:
            self.match_string = s
            for box in self.boxes:
                found, new_current_line, content = box.search(s)
                box.set_items(content)
                box.cur_line = new_current_line

    def boxes_for_path(self, initial_path: Sequence[str]) -> List[CustomListBox]:
        boxes = []
        index = 0
        while True:
            remaining_path = initial_path[index:]
            preferred_selection = None if len(remaining_path) == 0 else remaining_path[0]
            a_box = self.make_box_or_none(initial_path[:index], preferred_selection)
            if a_box is None:
                break
            # debug('boxes_for_path', path=initial_path[:index], box_choice=a_box.choice, box_cur_line=a_box.cur_line)
            boxes.append(a_box)
            index += 1
            if index > len(initial_path):
                break

        debug("boxes_for_path", initial_path=initial_path)
        for index, l in enumerate(boxes):
            if index == len(initial_path) - 1 or len(initial_path) == 0:
                l.focus = True
                break
            if index < len(initial_path):
                l.cur_line = l.choice = item_model.index_of_item_file_name(initial_path[index], l.items) or 0

        return boxes

    def expand_lists(self):
        index = len(self.boxes) - 1
        while True:
            # debug("expand_lists", index=index)
            if self.is_at_leaf(index):
                debug("expand_lists", index=index, is_at_leaf=True)
                break
            path = self.path(index)
            name = self.oracle.recall_chosen_name(path)
            index += 1
            a_list = self.make_box_or_none(path)
            # debug("expand_lists", index=index, a_list_not_none=a_list is not None)
            if a_list is None or a_list.cur_line is None:
                break
            self.boxes.append(a_list)
            if len(a_list.items) == 1:
                continue
            if name is None:
                break
        # debug("expand_lists", boxes_heights=[b.height for b in self.boxes])

    def activate_sibling(self, index):
        # debug("activate_sibling", index=index)
        self.boxes = self.boxes[: index + 1]
        self.expand_lists()
        self.memorize_choice_in_list(index, False)

    def try_to_go_in(self, index):
        # debug("try_to_go_in", index=index)
        is_at_leaf = self.is_at_leaf(index)
        # debug("try_to_go_in", is_at_leaf=is_at_leaf)
        not_last = index != len(self.boxes) - 1
        if not_last or is_at_leaf:
            return

        self.memorize_choice_in_list(index, False)

        new_box = self.make_box_or_none(self.path(index))
        if new_box is None:
            # debug("try_to_go_in", new_box=None)
            return

        debug("try_to_go_in", new_box_height=new_box.height)
        self.boxes.append(new_box)
        self.expand_lists()
        return True

    def make_box_or_none(self, path: Sequence[str], preferred: Optional[str] = None) -> Optional[CustomListBox]:
        # debug("make_box_or_none", path=path)
        items = self.entry_lister(path)
        if len(items) == 0:
            # debug("make_box_or_none", items_length=0)
            return None
        return self.make_box(path, items, preferred)

    def make_box(self, path: Sequence[str], items: Sequence[ListItem], preferred: Optional[str] = None):
        # debug("make_box", items=items, items_length=len(items), path=path)
        box = CustomListBox(
            item_model.max_item_text_length(items),
            len(items),
            items,
            path,
            lambda: self.match_string,
            lambda: self.match_string == self.search_string
        )
        last_name = self.oracle.recall_chosen_name(path) if not preferred else preferred
        choice = item_model.index_of_item_file_name(last_name, items)
        box.cur_line = box.choice = 0 if choice is None else choice
        return box

    def memorize_choice_in_list(self, index, persistent: bool):
        parent_path = [] if index == 0 else self.path(index - 1)
        self.oracle.memorize(parent_path, item_model.item_file_name(self.selected_item_in_list(index)), persistent)

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
        return [item_model.item_file_name(l.items[l.cur_line]) for l in self.boxes[: index + 1]]

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
