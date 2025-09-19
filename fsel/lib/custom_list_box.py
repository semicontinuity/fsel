from typing import Sequence

from datatools.tui.buffer.abstract_buffer_writer import AbstractBufferWriter
from picotui.widgets import WListBox

from .ansi import attr_italic, attr_strike_thru, attr_reversed, attr_crossed_out, attr_not_crossed_out, \
    attr_not_reversed, attr_color
from .colors import Colors
from .item_model import item_model
from .list_item import ListItem
from .logging import debug
from .paint_context import p_ctx
from .palette import palette
from .rich_text import Style, RichText


class CustomListBox(WListBox):
    def __init__(self, w, h, items: Sequence[ListItem], folder=None, search_string_supplier=lambda: '',
                 is_full_match_supplier=lambda: True):
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
        self.top_line = max(self.top_line, 0)  # becomes negative when search-filtering?

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

            p_ctx.paint_text(l[:display_from])

            attr_reversed()
            full_match = self.is_full_match_supplier()

            if not full_match:
                attr_crossed_out()

            p_ctx.paint_text(l[display_from: display_to])

            if not full_match:
                attr_not_crossed_out()

            attr_not_reversed()

            attr_color(_palette[Colors.C_IDX_REG_FG], _palette[Colors.C_IDX_BG])
            p_ctx.paint_text(l[display_to:])
        else:
            self.attr_reset()
            attr_italic(item_model.is_italic(item))
            attr_strike_thru(item_model.is_strike_thru(item))
            attr_color(_palette[Colors.C_IDX_REG_FG], _palette[Colors.C_IDX_BG])
            p_ctx.paint_text(l)

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

        # Construct RichText object
        rich_text: RichText = []

        if display_from != -1:
            # Text before match
            if display_from > 0:
                rich_text.append((l[:display_from], base_style))

            # Matched text
            match_style = base_style
            full_match = self.is_full_match_supplier()
            if not full_match:
                match_style = match_style.with_attr_flag(AbstractBufferWriter.MASK_CROSSED_OUT)

            rich_text.append((l[display_from:display_to], match_style))

            # Text after match
            if display_to < len(l):
                rich_text.append((l[display_to:], base_style))
        else:
            # No match, just regular text
            rich_text.append((l, base_style))

        # Render the RichText
        result = p_ctx.paint_rich_text(rich_text, 0, len(l))
        p_ctx.paint_text(result)

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
