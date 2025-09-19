from typing import Optional, List, AnyStr, Sequence


class Oracle:
    def memorize(self, path: List[AnyStr], name: AnyStr, persistent: bool):
        pass

    def recall_chosen_name(self, path: List[AnyStr]) -> Optional[AnyStr]:
        pass

    def recall_choice(self, path: Sequence[AnyStr], items) -> int:
        pass
