import sys
from typing import Sequence, Tuple

from fsel.lib.item_model import ItemModel
from fsel.lib.list_boxes import ListBoxes
from fsel.lib.list_item import ListItem
from fsel.lib.path_oracle import PathOracle
from fsel.lib.select_path_dialog import SelectPathDialog
from fsel.sdk import run_dialog

if __name__ == "__main__":
    class Lister:
        tree = {
            "": ("node1", "node2",),
            "node1": ("node11", "node12",)
        }

        def __call__(self, path: Sequence[str]) -> Sequence[ListItem]:
            return [
                ListItem(value, self.attribute(value))
                for value in Lister.tree[path[-1] if path else ""]
            ]

        def attribute(self, node: str) -> int:
            return ItemModel.FLAG_DIRECTORY if Lister.tree.get(node) else 0


    view = ListBoxes(Lister(), PathOracle({}, {}), [])

    exit_code, path = run_dialog(
        lambda screen_height, screen_width, cursor_y, cursor_x:
        SelectPathDialog(view, screen_width, screen_height, width=1000, height=0, x=0, y=cursor_y)
    )

    sys.exit(exit_code)
