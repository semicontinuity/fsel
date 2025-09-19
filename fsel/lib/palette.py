from stat import S_ISVTX, S_ISGID, S_ISUID

from .colors import Colors
from .item_model import ItemModel


def palette(attrs: int, focused_list: bool, focused_entry: bool) -> list[int]:
    """ category: one of C_IDX_* constants """

    if (attrs & ItemModel.FLAG_DIRECTORY) and (attrs & S_ISVTX):
        _palette = Colors.C_STICKY_FOLDER
    elif (attrs & ItemModel.FLAG_DIRECTORY) and (attrs & S_ISGID):
        _palette = Colors.C_SGID_FOLDER
    elif (attrs & ItemModel.FLAG_DIRECTORY) and (attrs & S_ISUID):
        _palette = Colors.C_SUID_FOLDER
    elif attrs & ItemModel.FLAG_DIRECTORY:
        _palette = Colors.C_FOLDER
    else:
        _palette = Colors.C_LEAF

    return _palette[2 * int(focused_list) + int(focused_entry)]
