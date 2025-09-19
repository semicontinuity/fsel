import sys

from picotui.screen import Screen


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

    def clear_box(self, left, top, width, height):
        # "\x1b[%s;%s;%s;%s$z" doesn't work
        s = b" " * width
        bottom = top + height
        while top < bottom:
            self.goto(left, top)
            self.clear_num_pos(width)
            top += 1


p_ctx = PaintContext()
