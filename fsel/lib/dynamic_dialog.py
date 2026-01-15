from picotui.screen import Screen
from picotui.widgets import Dialog

from fsel.lib.tui.paint_context import p_ctx


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
