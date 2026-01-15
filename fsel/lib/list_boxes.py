from typing import Optional, List, Callable, Sequence

from fsel.lib.list_item_info_service import list_item_info_service
from .list_item import ListItem
from .logging import debug
from .custom_list_box import CustomListBox
from .oracle import Oracle


class ListBoxes:
    entry_lister: Callable[[Sequence[str]], Sequence[ListItem]]
    boxes: List[CustomListBox]
    search_string: str = ''
    match_string: str = ''

    def __init__(self, entry_lister: Callable[[Sequence[str]], Sequence[ListItem]], oracle: Oracle, initial_path: List):
        debug('ListBoxes', initial_path=initial_path)
        self.entry_lister = entry_lister
        self.oracle = oracle
        self.boxes = self.boxes_for_path(initial_path)
        debug('ListBoxes', boxes=self.boxes)

    def search(self, s: str = ''):
        debug('ListBoxes.search', s=s)
        self.search_string = s

        found_somewhere = False
        for box in self.boxes:
            found, new_current_line, content = box.search(s)
            found_somewhere |= found
        debug('ListBoxes.search', found_somewhere=found_somewhere)

        if found_somewhere:
            self.match_string = s
            for box in self.boxes:
                found, new_current_line, content = box.search(s)
                box.set_items(content)
                box.cur_line = new_current_line

    def boxes_for_path(self, initial_path: Sequence[str]) -> List[CustomListBox]:
        boxes = []
        index = 0
        while True:
            remaining_path = initial_path[index:]
            preferred_selection = None if len(remaining_path) == 0 else remaining_path[0]
            a_box = self.make_box_or_none(initial_path[:index], preferred_selection)
            if a_box is None:
                break
            # debug('boxes_for_path', path=initial_path[:index], box_choice=a_box.choice, box_cur_line=a_box.cur_line)
            boxes.append(a_box)
            index += 1
            if index > len(initial_path):
                break

        debug("boxes_for_path", initial_path=initial_path)
        for index, l in enumerate(boxes):
            if index == len(initial_path) - 1 or len(initial_path) == 0:
                l.focus = True
                break
            if index < len(initial_path):
                l.cur_line = l.choice = list_item_info_service.index_of_item_file_name(initial_path[index], l.items) or 0

        return boxes

    def expand_lists(self):
        index = len(self.boxes) - 1
        while True:
            # debug("expand_lists", index=index)
            if self.is_at_leaf(index):
                debug("expand_lists", index=index, is_at_leaf=True)
                break
            path = self.path(index)
            name = self.oracle.recall_chosen_name(path)
            index += 1
            a_list = self.make_box_or_none(path)
            # debug("expand_lists", index=index, a_list_not_none=a_list is not None)
            if a_list is None or a_list.cur_line is None:
                break
            self.boxes.append(a_list)
            if len(a_list.items) == 1:
                continue
            if name is None:
                break
        # debug("expand_lists", boxes_heights=[b.height for b in self.boxes])

    def activate_sibling(self, index):
        # debug("activate_sibling", index=index)
        self.boxes = self.boxes[: index + 1]
        self.expand_lists()
        self.memorize_choice_in_list(index, False)

    def try_to_go_in(self, index):
        # debug("try_to_go_in", index=index)
        is_at_leaf = self.is_at_leaf(index)
        # debug("try_to_go_in", is_at_leaf=is_at_leaf)
        not_last = index != len(self.boxes) - 1
        if not_last or is_at_leaf:
            return

        self.memorize_choice_in_list(index, False)

        new_box = self.make_box_or_none(self.path(index))
        if new_box is None:
            # debug("try_to_go_in", new_box=None)
            return

        debug("try_to_go_in", new_box_height=new_box.height)
        self.boxes.append(new_box)
        self.expand_lists()
        return True

    def make_box_or_none(self, path: Sequence[str], preferred: Optional[str] = None) -> Optional[CustomListBox]:
        # debug("make_box_or_none", path=path)
        items = self.entry_lister(path)
        if len(items) == 0:
            # debug("make_box_or_none", items_length=0)
            return None
        return self.make_box(path, items, preferred)

    def make_box(self, path: Sequence[str], items: Sequence[ListItem], preferred: Optional[str] = None):
        # debug("make_box", items=items, items_length=len(items), path=path)
        box = CustomListBox(
            list_item_info_service.max_item_text_length(items),
            len(items),
            items,
            path,
            lambda: self.match_string,
            lambda: self.match_string == self.search_string
        )
        last_name = self.oracle.recall_chosen_name(path) if not preferred else preferred
        choice = list_item_info_service.index_of_item_file_name(last_name, items)
        box.cur_line = box.choice = 0 if choice is None else choice
        return box

    def memorize_choice_in_list(self, index, persistent: bool):
        parent_path = [] if index == 0 else self.path(index - 1)
        self.oracle.memorize(parent_path, list_item_info_service.item_file_name(self.selected_item_in_list(index)), persistent)

    def index_of_last_list(self):
        return len(self.boxes) - 1

    def is_at_leaf(self, index):
        return list_item_info_service.is_leaf(self.selected_item_in_list(index))

    def selected_item_in_list(self, index):
        return self.boxes[index].items[self.boxes[index].cur_line]

    def max_child_height(self):
        return max(len(child.items) for child in self.boxes)

    def is_empty(self):
        return len(self.boxes) == 0

    def path(self, index) -> List[str]:
        return [list_item_info_service.item_file_name(l.items[l.cur_line]) for l in self.boxes[: index + 1]]

    def items_path(self, index):
        return [l.items[l.cur_line] for l in self.boxes[: index + 1]]
