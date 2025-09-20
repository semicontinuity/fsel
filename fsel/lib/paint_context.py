import sys
from typing import AnyStr

from datatools.tui.ansi_str import ANSI_CMD_DEFAULT_FG, ANSI_CMD_ATTR_NOT_BOLD, ANSI_CMD_ATTR_BOLD, ANSI_CMD_DEFAULT_BG, \
    ANSI_CMD_ATTR_NOT_ITALIC, ANSI_CMD_ATTR_ITALIC, ANSI_CMD_ATTR_UNDERLINED, ANSI_CMD_ATTR_NOT_UNDERLINED, \
    ANSI_CMD_ATTR_CROSSED_OUT, ANSI_CMD_ATTR_NOT_CROSSED_OUT, ANSI_CMD_ATTR_INVERTED, \
    ANSI_CMD_ATTR_NOT_INVERTED
from datatools.tui.buffer.abstract_buffer_writer import AbstractBufferWriter
from datatools.tui.terminal import ansi_foreground_escape_code_auto, ansi_background_escape_code_auto
from picotui.screen import Screen

from fsel.lib.rich_text import RichText, Style


class PaintContext:
    """ Paint context is a "viewport", that allows to paint text with clipping """
    cur_x: int = sys.maxsize
    cur_y: int = sys.maxsize
    min_x: int = 0
    min_y: int = 0
    max_x: int = 0
    max_y: int = 0

    def attr_reset(self):
        Screen.attr_reset()

    def attr_reversed(self):
        Screen.wr("\x1b[7m")

    def attr_not_reversed(self):
        Screen.wr("\x1b[27m")

    def attr_crossed_out(self):
        Screen.wr("\x1b[9m")

    def attr_not_crossed_out(self):
        Screen.wr("\x1b[29m")

    def attr_italic(self, on: bool):
        Screen.wr("\x1b[3m" if on else "\x1b[23m")

    def attr_strike_thru(self, on: bool):
        Screen.wr("\x1b[9m" if on else "\x1b[29m")

    def attr_color(self, fg, bg=-1):
        if bg == -1:
            bg = fg >> 4
            fg &= 0xf

        if type(fg) is tuple:
            r, g, b = fg
            s = "\x1b[38;2;%d;%d;%d;" % (r, g, b)
        else:
            s = "\x1b[38;5;%d;" % (fg,)
        if type(bg) is tuple:
            r, g, b = bg
            s += "48;2;%d;%d;%dm" % (r, g, b)
        else:
            s += "48;5;%dm" % (bg,)

        Screen.wr(s)

    def goto(self, x: int, y: int):
        self.cur_x = x
        self.cur_y = y
        if self.min_x <= x < self.max_x and self.min_y <= y < self.max_y:
            Screen.goto(x, y)

    def clear_box(self, left, top, width, height):
        # "\x1b[%s;%s;%s;%s$z" doesn't work
        bottom = top + height
        while top < bottom:
            self.goto(left, top)
            self.clear_num_pos(width)
            top += 1

    def clear_num_pos(self, length: int):
        """ Clear the specified number of characters in the current line """
        x = self.cur_x
        new_x = x + length

        # Only clear, if cur_y is within allowed Y range
        if self.min_y <= self.cur_y < self.max_y:
            skip_before = max(0, self.min_x - self.cur_x)
            skip_after = max(0, new_x - self.max_x)
            limit_length = length - skip_after
            fill_length = limit_length - skip_before
            if fill_length > 0:
                if skip_before > 0:
                    Screen.goto(self.min_x, self.cur_y)
                Screen.wr("\x1b[%dX" % fill_length)
            if limit_length == skip_before:
                Screen.goto(new_x, self.cur_y)

        self.cur_x = new_x

    def paint_text(self, s: str):
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

    def paint_rich_text(self, rich_text: RichText):
        """Paint rich text from current position with clipping"""
        if self.min_y <= self.cur_y < self.max_y:
            x = self.cur_x
            
            for span in rich_text:
                text = span[0]
                style = span[1]
                
                # Calculate visible portion of text with clipping
                text_length = len(text)
                new_x = x + text_length
                
                before = max(0, self.min_x - x)
                after = max(0, new_x - self.max_x)
                to = text_length - after
                
                if to > before:
                    # Apply clipping to text content first
                    clipped_text = text[before:to]
                    
                    # Format the clipped text with style
                    formatted_text = self.paint_rich_text_span(style, clipped_text)
                    
                    # Position cursor and write formatted text
                    if before > 0:
                        Screen.goto(self.min_x, self.cur_y)
                    else:
                        Screen.goto(x, self.cur_y)
                    
                    Screen.wr(formatted_text)
                
                x = new_x
            
            self.cur_x = x
        else:
            # If outside vertical bounds, just update cursor position
            self.cur_x += sum(len(span[0]) for span in rich_text)

    def paint_rich_text_span(self, style: Style, text: AnyStr) -> AnyStr:
        print('paint_rich_text_span', style, text)
        result = text
        if style.fg is not None:
            result = ansi_foreground_escape_code_auto(style.fg) + result + ANSI_CMD_DEFAULT_FG
        if style.bg is not None:
            result = ansi_background_escape_code_auto(style.bg) + result + ANSI_CMD_DEFAULT_BG
        if style.attr & AbstractBufferWriter.MASK_BOLD != 0:
            result = ANSI_CMD_ATTR_BOLD + result + ANSI_CMD_ATTR_NOT_BOLD
        if style.attr & AbstractBufferWriter.MASK_ITALIC != 0:
            result = ANSI_CMD_ATTR_ITALIC + result + ANSI_CMD_ATTR_NOT_ITALIC
        if style.attr & AbstractBufferWriter.MASK_UNDERLINED != 0:
            result = ANSI_CMD_ATTR_UNDERLINED + result + ANSI_CMD_ATTR_NOT_UNDERLINED
        if style.attr & AbstractBufferWriter.MASK_CROSSED_OUT != 0:
            result = ANSI_CMD_ATTR_CROSSED_OUT + result + ANSI_CMD_ATTR_NOT_CROSSED_OUT
        if style.attr & AbstractBufferWriter.MASK_BG_EMPHASIZED != 0:
            result = ANSI_CMD_ATTR_INVERTED + result + ANSI_CMD_ATTR_NOT_INVERTED
        print('paint_rich_text_span', style, repr(result))
        return result


p_ctx = PaintContext()
