import sys
from typing import AnyStr

from datatools.tui.ansi_str import ANSI_CMD_DEFAULT_FG, ANSI_CMD_ATTR_NOT_BOLD, ANSI_CMD_ATTR_BOLD, ANSI_CMD_DEFAULT_BG, \
    ANSI_CMD_ATTR_NOT_ITALIC, ANSI_CMD_ATTR_ITALIC, ANSI_CMD_ATTR_UNDERLINED, ANSI_CMD_ATTR_NOT_UNDERLINED
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

    def paint_rich_text(self, rich_text: RichText, start: int, end: int) -> AnyStr:
        result = ''
        span_start = 0

        for span in rich_text:
            span_end = span_start + len(span[0])
            if span_end > start:
                if end <= span_start:
                    break

                from_x = max(start, span_start)
                to_x = min(end, span_start + len(span[0]))
                text = span[0][from_x - span_start:to_x - span_start]
                result += self.paint_rich_text_span(span[1], text)
            span_start = span_end

        return result + ' ' * (end - max(start, span_start))

    def paint_rich_text_span(self, style: Style, text: AnyStr) -> AnyStr:
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
        return result


p_ctx = PaintContext()
