from datatools.tui.buffer.abstract_buffer_writer import AbstractBufferWriter

from fsel.lib.tui.colors import Color
from fsel.lib.tui.paint_context import p_ctx
from fsel.lib.tui.style import Style


def main():
    p_ctx.min_x = 10
    p_ctx.min_y = 10
    p_ctx.max_x = 20
    p_ctx.max_y = 20

    p_ctx.attr_color(fg=Color.B_YELLOW, bg=Color.BLUE)
    p_ctx.clear_box(0, 0, 30, 30)

    p_ctx.goto(6, 11)
    p_ctx.attr_italic(on=True)
    p_ctx.paint_text('The quick brown fox jumps over the lazy dog')
    p_ctx.attr_reset()

    p_ctx.goto(10, 12)
    t = [
        ('Hello', Style(fg=Color.B_RED)),
        ('World', Style(bg=Color.CYAN)),
    ]
    p_ctx.paint_rich_text(t)

    p_ctx.goto(9, 13)
    t = [
        ('Hello', Style(attr=AbstractBufferWriter.MASK_CROSSED_OUT, fg=Color.B_RED)),
        ('World', Style(bg=Color.CYAN)),
    ]
    p_ctx.paint_rich_text(t)

    p_ctx.goto(11, 14)
    t = [
        ('Hello', Style(attr=AbstractBufferWriter.MASK_BG_EMPHASIZED, fg=Color.B_RED)),
        ('World', Style(bg=Color.CYAN)),
    ]
    p_ctx.paint_rich_text(t)

    p_ctx.attr_reset()


if __name__ == "__main__":
    main()
    