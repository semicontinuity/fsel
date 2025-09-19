# This copy is more up-to-date

from dataclasses import dataclass
from typing import Sequence, Tuple, AnyStr
from typing import TypeAlias


@dataclass
class Style:
    attr: int = 0
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


RichTextSpan: TypeAlias = Tuple[AnyStr, Style]
RichText: TypeAlias = list[RichTextSpan]
