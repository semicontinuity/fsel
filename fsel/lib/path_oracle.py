from typing import Optional, List, Dict, AnyStr, Sequence

from .oracle import Oracle


class PathOracle(Oracle):
    def __init__(self, root_history: Dict, usage_stats: Dict):
        self.root_history = root_history
        self.usage_stats = usage_stats
        self.visit_history = {}
        self.session_stats = {}

    def memorize(self, path: List[AnyStr], name: AnyStr, persistent: bool):
        history = self.root_history if persistent else self.visit_history
        history[self.string_path(path)] = name
        stat_path = []
        stat_path += path
        stat_path.append(name)
        stat_path.append('.') # '.' is a special entry for counter
        if persistent:
            self.incr(self.usage_stats, stat_path)
        # self.incr(self.usage_stats if persistent else self.session_stats, stat_path)

    def recall_chosen_name(self, path: List[AnyStr]) -> Optional[AnyStr]:
        # string_path = self.string_path(path)
        # return self.visit_history.get(string_path) or self.root_history.get(string_path)
        entry = self.get_entry(self.usage_stats, path)
        if entry is not None:
            return self.most_frequent_in(entry)
        return None

    def most_frequent_in(self, entry: Dict) -> Optional[AnyStr]:
        top_f = 0
        result = None
        for k, v in entry.items():
            if k != '.':
                f = v['.']
                if f > top_f:
                    top_f = f
                    result = k
        return result

    def incr(self, stats: Dict, path: List):
        if len(path) == 1:
            value = stats.get(path[0]) or 0
            stats[path[0]] = value + 1
        else:
            entry = stats.get(path[0])
            if entry is None:
                entry = {}
                stats[path[0]] = entry

            self.incr(entry, path[1:])

    def get_entry(self, stats: Dict, path: List):
        if len(path) == 0:
            return stats
        else:
            entry = stats.get(path[0])
            return None if entry is None else self.get_entry(entry, path[1:])

    @staticmethod
    def string_path(path: Sequence):
        return '/'.join(path)
