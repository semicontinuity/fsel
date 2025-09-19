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


def rich_text_length(rich_text: RichText) -> int:
    """Calculate the visible length of a rich text object by summing the lengths of all text spans."""
    return sum(len(text) for text, _ in rich_text)


def rich_text_to_plain(rich_text: RichText) -> str:
    """Convert a rich text object to plain text by concatenating all text spans."""
    return ''.join(text for text, _ in rich_text)
