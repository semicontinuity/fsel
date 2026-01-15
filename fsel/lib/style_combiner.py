from stat import S_ISVTX, S_ISGID, S_ISUID

from datatools.tui.buffer.abstract_buffer_writer import AbstractBufferWriter

from fsel.lib.list_item_info_service import ListItemInfoService
from fsel.lib.tui.palette import Palette
from fsel.lib.tui.style import Style


class StyleCombiner:
    palette: list[int]

    def __init__(self, attrs: int, focused_list: bool, focused_entry: bool) -> None:
        self.palette = StyleCombiner._get_palette(attrs, focused_list, focused_entry)

    @staticmethod
    def _get_palette(attrs: int, focused_list: bool, focused_entry: bool) -> list[int]:
        """ category: one of C_IDX_* constants """

        if (attrs & ListItemInfoService.FLAG_DIRECTORY) and (attrs & S_ISVTX):
            _palette = Palette.STICKY_FOLDER
        elif (attrs & ListItemInfoService.FLAG_DIRECTORY) and (attrs & S_ISGID):
            _palette = Palette.SGID_FOLDER
        elif (attrs & ListItemInfoService.FLAG_DIRECTORY) and (attrs & S_ISUID):
            _palette = Palette.SUID_FOLDER
        elif attrs & ListItemInfoService.FLAG_DIRECTORY:
            _palette = Palette.FOLDER
        else:
            _palette = Palette.LEAF

        return _palette[2 * int(focused_list) + int(focused_entry)]

    def match_style_for(self, style):
        return self.style_for(AbstractBufferWriter.MASK_BG_EMPHASIZED, style)

    def style_for(self, base_attr, style):
        return Style(
            attr=(style.attr | base_attr),
            fg=style.fg if style.fg is not None else self.palette[Palette.C_IDX_REG_FG],
            bg=style.bg if style.bg is not None else self.palette[Palette.C_IDX_BG]
        )
