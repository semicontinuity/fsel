from typing import Sequence

from picotui.widgets import WListBox

from fsel.lib.list_item_info_service import list_item_info_service
from fsel.lib.tui.paint_context import p_ctx
from fsel.lib.tui.rich_text import RichText, rich_text_length, rich_text_to_plain
from .list_item import ListItem
from .logging import debug
from fsel.lib.style_combiner import StyleCombiner
from .tui.attribute import Attribute


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
            self.show_real_line(item, self.cur_line == i)

    def show_real_line(self, item: ListItem, is_focused_item: bool):
        """Alternative implementation of show_real_line using RichText"""
        # Get the rich text representation of the item
        rich_text = list_item_info_service.item_rich_text(item)
        item_attrs = list_item_info_service.attrs(item)

        # Get palette for this item
        combiner = StyleCombiner(attrs=item_attrs, focused_list=self.focus, focused_entry=is_focused_item)
        
        # Create base style attributes
        base_attr = 0
        if list_item_info_service.is_italic(item):
            base_attr |= Attribute.MASK_ITALIC
        if list_item_info_service.is_strike_thru(item):
            base_attr |= Attribute.MASK_CROSSED_OUT

        # Apply palette colors and attributes to each span in the rich text
        styled_rich_text: RichText = []
        for text, style in rich_text:
            # Create a new style that combines the original style with our palette colors
            new_style = combiner.style_for(base_attr, style)
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
                        match_style = combiner.match_style_for(style)

                        # Add crossed out attribute if not a full match
                        full_match = self.is_full_match_supplier()
                        if not full_match:
                            match_style = match_style.with_attr_flag(Attribute.MASK_CROSSED_OUT)
                        
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
            debug('CustomListBox.search', s=s, i=i, item_file_name=list_item_info_service.item_file_name(item))
            is_current = item == cur_item
            is_match = list_item_info_service.item_file_name(item).find(s) >= 0
            if is_match:
                debug('CustomListBox.search', found=True)
                found = True
            if is_current:
                debug('CustomListBox.search', cur_line=self.cur_line)
                new_current_line = len(content)
            if is_match or is_current:
                content.append(item)

        return found, new_current_line, content
