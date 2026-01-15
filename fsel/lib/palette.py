from stat import S_ISVTX, S_ISGID, S_ISUID

from .colors import Colors
from .list_item_info_service import ListItemInfoService


class Palette:
    C_STICKY_FOLDER = [
        # non focused list; non highlighted entry
        [Colors.BLACK, Colors.B_GREEN, Colors.B_RED],
        # non focused list; highlighted entry
        [Colors.BLUE, Colors.B_GREEN, Colors.B_RED],
        # focused list; non highlighted entry
        [Colors.BLACK, Colors.B_GREEN, Colors.B_RED],
        # focused list; highlighted entry
        [Colors.CYAN, Colors.B_GREEN, Colors.B_RED]
    ]

    C_SGID_FOLDER = [
        # non focused list; non highlighted entry
        [Colors.BLACK, Colors.B_YELLOW, Colors.B_RED],
        # non focused list; highlighted entry
        [Colors.BLUE, Colors.B_YELLOW, Colors.B_RED],
        # focused list; non highlighted entry
        [Colors.BLACK, Colors.B_YELLOW, Colors.B_RED],
        # focused list; highlighted entry
        [Colors.CYAN, Colors.B_YELLOW, Colors.B_RED]
    ]

    C_SUID_FOLDER = [
        # non focused list; non highlighted entry
        [Colors.BLACK, (192, 48, 48), (255, 64, 64)],
        # non focused list; highlighted entry
        [Colors.BLUE, (192, 48, 48), (255, 64, 64)],
        # focused list; non highlighted entry
        [Colors.BLACK, (192, 48, 48), (255, 64, 64)],
        # focused list; highlighted entry
        [Colors.CYAN, (192, 48, 48), (255, 64, 64)]
    ]

    C_FOLDER = [
        # non focused list; non highlighted entry
        [Colors.BLACK, Colors.B_WHITE, Colors.B_RED],
        # non focused list; highlighted entry
        [Colors.BLUE, Colors.B_WHITE, Colors.B_RED],
        # focused list; non highlighted entry
        [Colors.BLACK, Colors.B_WHITE, Colors.B_RED],
        # focused list; highlighted entry
        [Colors.CYAN, Colors.B_WHITE, Colors.B_RED]
    ]

    C_LEAF = [
        # non focused list; non highlighted entry
        [Colors.BLACK, Colors.GRAY, Colors.B_RED],
        # non focused list; highlighted entry
        [Colors.BLUE, Colors.GRAY, Colors.B_RED],
        # focused list; non highlighted entry
        [Colors.BLACK, Colors.GRAY, Colors.B_RED],
        # focused list; highlighted entry
        [Colors.CYAN, Colors.BLACK, Colors.B_RED]
    ]


def palette(attrs: int, focused_list: bool, focused_entry: bool) -> list[int]:
    """ category: one of C_IDX_* constants """

    if (attrs & ListItemInfoService.FLAG_DIRECTORY) and (attrs & S_ISVTX):
        _palette = Palette.C_STICKY_FOLDER
    elif (attrs & ListItemInfoService.FLAG_DIRECTORY) and (attrs & S_ISGID):
        _palette = Palette.C_SGID_FOLDER
    elif (attrs & ListItemInfoService.FLAG_DIRECTORY) and (attrs & S_ISUID):
        _palette = Palette.C_SUID_FOLDER
    elif attrs & ListItemInfoService.FLAG_DIRECTORY:
        _palette = Palette.C_FOLDER
    else:
        _palette = Palette.C_LEAF

    return _palette[2 * int(focused_list) + int(focused_entry)]
