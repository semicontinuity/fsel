from stat import S_ISVTX, S_ISGID, S_ISUID

from .colors import Colors
from .list_item_info_service import ListItemInfoService


def palette(attrs: int, focused_list: bool, focused_entry: bool) -> list[int]:
    """ category: one of C_IDX_* constants """

    if (attrs & ListItemInfoService.FLAG_DIRECTORY) and (attrs & S_ISVTX):
        _palette = Colors.C_STICKY_FOLDER
    elif (attrs & ListItemInfoService.FLAG_DIRECTORY) and (attrs & S_ISGID):
        _palette = Colors.C_SGID_FOLDER
    elif (attrs & ListItemInfoService.FLAG_DIRECTORY) and (attrs & S_ISUID):
        _palette = Colors.C_SUID_FOLDER
    elif attrs & ListItemInfoService.FLAG_DIRECTORY:
        _palette = Colors.C_FOLDER
    else:
        _palette = Colors.C_LEAF

    return _palette[2 * int(focused_list) + int(focused_entry)]
