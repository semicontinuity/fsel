from typing import List

from .dynamic_dialog import DynamicDialog


class AbstractSelectionDialog(DynamicDialog):
    def items_path(self) -> List:
        pass
