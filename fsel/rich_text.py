from dataclasses import dataclass
from typing import Optional, Sequence, Tuple, AnyStr, List

from datatools.tui.ansi_str import ANSI_CMD_DEFAULT_FG, ANSI_CMD_ATTR_NOT_BOLD, ANSI_CMD_ATTR_BOLD, ANSI_CMD_DEFAULT_BG, \
    ANSI_CMD_ATTR_NOT_ITALIC, ANSI_CMD_ATTR_ITALIC, ANSI_CMD_ATTR_UNDERLINED, ANSI_CMD_ATTR_NOT_UNDERLINED
from datatools.tui.buffer.abstract_buffer_writer import AbstractBufferWriter
from datatools.tui.terminal import ansi_foreground_escape_code, ansi_background_escape_code


@dataclass
class Style:
    attr: int = 0
    fg: Optional[Sequence[int]] = None
    bg: Optional[Sequence[int]] = None

    def with_attr(self, attr: int):
        self.attr = attr
        return self


def render_substr(spans: List[Tuple[AnyStr, Style]], start: int, end: int) -> AnyStr:
    result = ''
    span_start = 0

    for span in spans:
        span_end = span_start + len(span[0])
        if span_end > start:
            if end <= span_start:
                break

            from_x = max(start, span_start)
            to_x = min(end, span_start + len(span[0]))
            text = span[0][from_x - span_start:to_x - span_start]
            result += render_styled(span[1], text)
        span_start = span_end

    return result + ' ' * (end - max(start, span_start))


def render_styled(style: Style, text: AnyStr) -> AnyStr:
    result = text
    if style.fg is not None:
        result = ansi_foreground_escape_code(*style.fg) + result + ANSI_CMD_DEFAULT_FG
    if style.bg is not None:
        result = ansi_background_escape_code(*style.bg) + result + ANSI_CMD_DEFAULT_BG
    if style.attr & AbstractBufferWriter.MASK_BOLD != 0:
        result = ANSI_CMD_ATTR_BOLD + result + ANSI_CMD_ATTR_NOT_BOLD
    if style.attr & AbstractBufferWriter.MASK_ITALIC != 0:
        result = ANSI_CMD_ATTR_ITALIC + result + ANSI_CMD_ATTR_NOT_ITALIC
    if style.attr & AbstractBufferWriter.MASK_UNDERLINED != 0:
        result = ANSI_CMD_ATTR_UNDERLINED + result + ANSI_CMD_ATTR_NOT_UNDERLINED
    return result
