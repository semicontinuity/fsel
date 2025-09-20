from typing import Sequence

from datatools.tui.buffer.abstract_buffer_writer import AbstractBufferWriter
from picotui.widgets import WListBox

from .colors import Colors
from .item_model import item_model
from .list_item import ListItem
from .logging import debug
from .paint_context import p_ctx
from .palette import palette
from .rich_text import Style, RichText, rich_text_length, rich_text_to_plain


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
            p_ctx.attr_reset()
            p_ctx.clear_num_pos(self.width)
            p_ctx.attr_reset()
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
            p_ctx.attr_reset()
            p_ctx.attr_italic(item_model.is_italic(item))
            p_ctx.attr_strike_thru(item_model.is_strike_thru(item))
            p_ctx.attr_color(fg=_palette[Colors.C_IDX_REG_FG], bg=_palette[Colors.C_IDX_BG])

            p_ctx.paint_text(l[:display_from])

            p_ctx.attr_reversed()
            full_match = self.is_full_match_supplier()

            if not full_match:
                p_ctx.attr_crossed_out()

            p_ctx.paint_text(l[display_from: display_to])

            if not full_match:
                p_ctx.attr_not_crossed_out()

            p_ctx.attr_not_reversed()

            p_ctx.attr_color(_palette[Colors.C_IDX_REG_FG], _palette[Colors.C_IDX_BG])
            p_ctx.paint_text(l[display_to:])
        else:
            p_ctx.attr_reset()
            p_ctx.attr_italic(item_model.is_italic(item))
            p_ctx.attr_strike_thru(item_model.is_strike_thru(item))
            p_ctx.attr_color(_palette[Colors.C_IDX_REG_FG], _palette[Colors.C_IDX_BG])
            p_ctx.paint_text(l)

        p_ctx.clear_num_pos(self.width - len(l))
        p_ctx.attr_reset()

    def show_real_line2(self, item: ListItem, i):
        """Alternative implementation of show_real_line using RichText"""
        # Get the rich text representation of the item
        rich_text = item_model.item_rich_text(item)
        
        # Get palette for this item
        _palette = palette(item_model.attrs(item), self.focus, self.cur_line == i)
        
        # Create base style attributes
        base_attr = 0
        if item_model.is_italic(item):
            base_attr |= AbstractBufferWriter.MASK_ITALIC
            
        # Apply palette colors and attributes to each span in the rich text
        styled_rich_text: RichText = []
        for text, style in rich_text:
            # Create a new style that combines the original style with our palette colors
            new_style = Style(
                attr=style.attr | base_attr,
                fg=style.fg if style.fg is not None else _palette[Colors.C_IDX_REG_FG],
                bg=style.bg if style.bg is not None else _palette[Colors.C_IDX_BG]
            )
            styled_rich_text.append((text, new_style))
        
        # Handle search highlighting if needed
        match_string = self.match_string_supplier()
        if match_string and len(match_string) > 0:
            # Convert rich text to plain text for searching
            plain_text = rich_text_to_plain(styled_rich_text)
            
            # Find match in plain text
            match_from = plain_text.find(match_string)
            if match_from >= 0:
                match_to = match_from + len(match_string)
                
                # Limit to width if needed
                plain_text = plain_text[:self.width]
                match_from = min(match_from, self.width)
                match_to = min(match_to, self.width)
                
                debug('show_real_line2', width=self.width, plain_text=plain_text, 
                      match_from=match_from, match_to=match_to)
                
                # Create a new rich text with highlighting for the match
                highlighted_rich_text: RichText = []
                current_pos = 0
                
                for text, style in styled_rich_text:
                    text_start = current_pos
                    text_end = text_start + len(text)
                    
                    # Check if this span overlaps with the match
                    if text_end > match_from and text_start < match_to:
                        # Calculate the overlap
                        overlap_start = max(text_start, match_from) - text_start
                        overlap_end = min(text_end, match_to) - text_start
                        
                        # Add text before match if any
                        if overlap_start > 0:
                            highlighted_rich_text.append((text[:overlap_start], style))
                        
                        # Add matched text with reversed style
                        match_text = text[overlap_start:overlap_end]
                        match_style = Style(
                            attr=style.attr | AbstractBufferWriter.MASK_BG_EMPHASIZED,
                            fg=style.fg if style.fg is not None else _palette[Colors.C_IDX_REG_FG],
                            bg=style.bg if style.bg is not None else _palette[Colors.C_IDX_BG]
                        )
                        
                        # Add crossed out attribute if not a full match
                        full_match = self.is_full_match_supplier()
                        if not full_match:
                            match_style = match_style.with_attr_flag(AbstractBufferWriter.MASK_CROSSED_OUT)
                        
                        highlighted_rich_text.append((match_text, match_style))
                        
                        # Add text after match if any
                        if overlap_end < len(text):
                            highlighted_rich_text.append((text[overlap_end:], style))
                    else:
                        # This span doesn't overlap with the match
                        highlighted_rich_text.append((text, style))
                    
                    current_pos = text_end
                
                # Use the highlighted rich text
                styled_rich_text = highlighted_rich_text
        
        # Render the RichText
        p_ctx.paint_rich_text(styled_rich_text)
        
        # Calculate total visible length of the rich text
        visible_length = rich_text_length(styled_rich_text)
        
        # Clear the rest of the line
        p_ctx.clear_num_pos(self.width - visible_length)
        p_ctx.attr_reset()

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
