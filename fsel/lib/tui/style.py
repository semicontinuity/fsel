from dataclasses import dataclass
from typing import Sequence


@dataclass
class Style:
    attr: int = 0   # Collection of flags from AbstractBufferWriter
    fg: int | Sequence[int] | None = None
    bg: int | Sequence[int] | None = None

    def with_attr(self, attr: int):
        return Style(
            attr = attr,
            fg = self.fg,
            bg = self.bg,
        )

    def with_attr_flag(self, flag: int):
        return self.with_attr(self.attr | flag)