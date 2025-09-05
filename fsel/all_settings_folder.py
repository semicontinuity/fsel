import json
import os
from typing import Set, AnyStr


class AllSettingsFolder:
    roots: Set[str] = set()

    def __init__(self, all_settings_folder: str):
        os.makedirs(all_settings_folder, exist_ok=True)
        self.all_settings_folder = all_settings_folder
        for entry in os.scandir(all_settings_folder):
            if entry.is_file():
                self.roots.add(entry.name.replace('\\', '/'))

    def load_settings(self, root: AnyStr):
        try:
            with open(self.settings_file(root)) as json_file:
                return json.load(json_file)
        except:
            return {}

    def save(self, settings, root: AnyStr):
        try:
            with open(self.settings_file(root), 'w') as f:
                json.dump(settings, f, indent=2, sort_keys=True)
        except:
            pass

    def settings_file(self, root):
        return self.all_settings_folder + '/' + root.replace('/', '\\')
