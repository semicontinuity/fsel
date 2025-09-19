from typing import Iterable

from fsel.list_item import ListItem


class ItemModel:
    FLAG_DIRECTORY = 0x8000
    FLAG_ITALIC = 0x10000
    FLAG_STRIKE_THRU = 0x20000

    def attrs(self, item: ListItem):
        return item.attrs

    def is_leaf(self, item: ListItem):
        return (item.attrs & ItemModel.FLAG_DIRECTORY) == 0

    def is_italic(self, item: ListItem):
        return (item.attrs & ItemModel.FLAG_ITALIC) != 0

    def is_strike_thru(self, item: ListItem):
        return (item.attrs & ItemModel.FLAG_STRIKE_THRU) != 0

    def max_item_text_length(self, items):
        return max(self.item_text_length(item) for item in items)

    def item_text(self, item: ListItem) -> str:
        if item.description is not None:
            return item.name + ' ' + "\033[38;5;220m" + item.description + "\033[0m"
        else:
            return item.name

    # TODO: later, text is cut to this length - but it includes ANSI escapes, so only part of text is visible
    def item_text_length(self, item: ListItem) -> int:
        if item.description is not None:
            return len(item.name) + len(' ') + len(item.description)
        else:
            return len(item.name)

    def item_file_name(self, item: ListItem) -> str:
        return item.name

    def index_of_item_file_name(self, file_name: str, items: Iterable[ListItem]) -> int|None:
        for i, item in enumerate(items):
            if file_name == self.item_file_name(item):
                return i


item_model = ItemModel()
