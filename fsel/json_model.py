from typing import List, AnyStr


class JsonModel:
    def __init__(self, data):
        self.data = data

    def list_items(self, path: List[AnyStr]):
        return self.list_items_of(self.data, path)

    def list_items_of(self, j, path: List[AnyStr]):
        if not path:
            if isinstance(j, dict):
                return [[k, False] for k in j.keys()]
            elif isinstance(j, list):
                return [[str(k), False] for k in range(len(j))]
            else:
                return []
        else:
            return self.list_items_of(self.resolve(j, path[0]), path[1:])

    def resolve(self, j, s: AnyStr):
        if isinstance(j, dict):
            return j[s]
        if isinstance(j, list):
            return j[int(s)]
