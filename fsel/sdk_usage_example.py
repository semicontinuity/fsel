import sys
from typing import Sequence, Tuple

from fsel.sdk import run_dialog, SelectPathDialog, PathOracle, ListBoxes, ItemModel

if __name__ == "__main__":
    class Lister:
        tree = {
            "": ("node1", "node2",),
            "node1": ("node11", "node12",)
        }

        def __call__(self, path: Sequence[str]) -> Sequence[Tuple[str, int]]:
            """ Each item is a tuple; last element of tuple is int with item attributes (same as in st_mode) """
            return tuple(
                (value, self.attribute(value))
                for value in Lister.tree[path[-1] if path else ""]
            )

        def attribute(self, node: str) -> int:
            return ItemModel.FLAG_DIRECTORY if Lister.tree.get(node) else 0


    view = ListBoxes(Lister(), PathOracle({}, {}), [])

    exit_code, path = run_dialog(
        lambda screen_height, screen_width, cursor_y, cursor_x:
        SelectPathDialog(view, screen_width, screen_height, width=1000, height=0, x=0, y=cursor_y)
    )

    sys.exit(exit_code)
