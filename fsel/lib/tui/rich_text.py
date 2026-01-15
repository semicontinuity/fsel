# This copy is more up-to-date

from typing import Tuple, AnyStr
from typing import TypeAlias

from fsel.lib.tui.style import Style

RichTextSpan: TypeAlias = Tuple[AnyStr, Style]
RichText: TypeAlias = list[RichTextSpan]


def rich_text_length(rich_text: RichText) -> int:
    """Calculate the visible length of a rich text object by summing the lengths of all text spans."""
    return sum(len(text) for text, _ in rich_text)


def rich_text_to_plain(rich_text: RichText) -> str:
    """Convert a rich text object to plain text by concatenating all text spans."""
    return ''.join(text for text, _ in rich_text)
