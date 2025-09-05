from typing import Iterable


class ItemModel:
    FLAG_DIRECTORY = 0x8000
    FLAG_ITALIC = 0x10000

    def attrs(self, item: tuple[str, int, str|None]):
        return item[1]

    def is_leaf(self, item: tuple[str, int, str|None]):
        return (item[1] & ItemModel.FLAG_DIRECTORY) == 0

    def is_italic(self, item: tuple[str, int, str|None]):
        return (item[1] & ItemModel.FLAG_ITALIC) != 0

    def max_item_text_length(self, items):
        return max(self.item_text_length(item) for item in items)

    def item_text(self, item: tuple[str, int, str|None]) -> str:
        if item[2] is not None:
            return item[0] + ' ' + "\033[38;5;220m" + item[2] + "\033[0m"
        else:
            return item[0]

    # TODO: later, text is cut to this length - but it includes ANSI escapes, so only part of text is visible
    def item_text_length(self, item: tuple[str, int, str|None]) -> int:
        if item[2] is not None:
            return len(item[0]) + len(' ') + len(item[2])
        else:
            return len(item[0])

    def item_file_name(self, item: tuple[str, int, str|None]) -> str:
        return item[0]

    def index_of_item_file_name(self, file_name: str, items: Iterable[tuple[str, int, str | None]]) -> int|None:
        for i, item in enumerate(items):
            if file_name == self.item_file_name(item):
                return i


item_model = ItemModel()
