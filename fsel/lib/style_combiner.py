from stat import S_ISVTX, S_ISGID, S_ISUID

from fsel.lib.list_item_info_service import ListItemInfoService
from fsel.lib.tui.attribute import Attribute
from fsel.lib.tui.color import Color
from fsel.lib.tui.style import Style


class StyleCombiner:
    class Colors:
        C_IDX_BG = 0
        C_IDX_REG_FG = 1
        C_IDX_MATCH_FG = 2  # unused

        STICKY_FOLDER = [
            # non focused list; non highlighted entry
            [Color.BLACK, Color.B_GREEN, Color.B_RED],
            # non focused list; highlighted entry
            [Color.BLUE, Color.B_GREEN, Color.B_RED],
            # focused list; non highlighted entry
            [Color.BLACK, Color.B_GREEN, Color.B_RED],
            # focused list; highlighted entry
            [Color.CYAN, Color.B_GREEN, Color.B_RED]
        ]

        SGID_FOLDER = [
            # non focused list; non highlighted entry
            [Color.BLACK, Color.B_YELLOW, Color.B_RED],
            # non focused list; highlighted entry
            [Color.BLUE, Color.B_YELLOW, Color.B_RED],
            # focused list; non highlighted entry
            [Color.BLACK, Color.B_YELLOW, Color.B_RED],
            # focused list; highlighted entry
            [Color.CYAN, Color.B_YELLOW, Color.B_RED]
        ]

        SUID_FOLDER = [
            # non focused list; non highlighted entry
            [Color.BLACK, (192, 48, 48), (255, 64, 64)],
            # non focused list; highlighted entry
            [Color.BLUE, (192, 48, 48), (255, 64, 64)],
            # focused list; non highlighted entry
            [Color.BLACK, (192, 48, 48), (255, 64, 64)],
            # focused list; highlighted entry
            [Color.CYAN, (192, 48, 48), (255, 64, 64)]
        ]

        FOLDER = [
            # non focused list; non highlighted entry
            [Color.BLACK, Color.B_WHITE, Color.B_RED],
            # non focused list; highlighted entry
            [Color.BLUE, Color.B_WHITE, Color.B_RED],
            # focused list; non highlighted entry
            [Color.BLACK, Color.B_WHITE, Color.B_RED],
            # focused list; highlighted entry
            [Color.CYAN, Color.B_WHITE, Color.B_RED]
        ]

        LEAF = [
            # non focused list; non highlighted entry
            [Color.BLACK, Color.GRAY, Color.B_RED],
            # non focused list; highlighted entry
            [Color.BLUE, Color.GRAY, Color.B_RED],
            # focused list; non highlighted entry
            [Color.BLACK, Color.GRAY, Color.B_RED],
            # focused list; highlighted entry
            [Color.CYAN, Color.BLACK, Color.B_RED]
        ]

    colors: list[int]

    def __init__(self, attrs: int, focused_list: bool, focused_entry: bool) -> None:
        self.colors = StyleCombiner._get_colors(attrs, focused_list, focused_entry)

    @staticmethod
    def _get_colors(attrs: int, focused_list: bool, focused_entry: bool) -> list[int]:
        """ category: one of C_IDX_* constants """

        if (attrs & ListItemInfoService.FLAG_DIRECTORY) and (attrs & S_ISVTX):
            _colors = StyleCombiner.Colors.STICKY_FOLDER
        elif (attrs & ListItemInfoService.FLAG_DIRECTORY) and (attrs & S_ISGID):
            _colors = StyleCombiner.Colors.SGID_FOLDER
        elif (attrs & ListItemInfoService.FLAG_DIRECTORY) and (attrs & S_ISUID):
            _colors = StyleCombiner.Colors.SUID_FOLDER
        elif attrs & ListItemInfoService.FLAG_DIRECTORY:
            _colors = StyleCombiner.Colors.FOLDER
        else:
            _colors = StyleCombiner.Colors.LEAF

        return _colors[2 * int(focused_list) + int(focused_entry)]

    def match_style_for(self, style):
        return self.style_for(Attribute.MASK_BG_EMPHASIZED, style)

    def style_for(self, base_attr, style):
        return Style(
            attr=(style.attr | base_attr),
            fg=style.fg if style.fg is not None else self.colors[StyleCombiner.Colors.C_IDX_REG_FG],
            bg=style.bg if style.bg is not None else self.colors[StyleCombiner.Colors.C_IDX_BG]
        )
