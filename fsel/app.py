import json
import os
import sys
from typing import Callable, List, Tuple, Dict, AnyStr

from fsel.sdk import FsListFiles, update_recents, run_dialog, ItemSelectionDialog, full_path, item_model, field_or_else, \
    FsModel, ListBoxes, SelectPathDialog, Oracle


def load_settings():
    try:
        with open(settings_file()) as json_file:
            return json.load(json_file)
    except:
        return {}


def save_settings(settings):
    try:
        with open(settings_file(), 'w') as f:
            json.dump(settings, f, indent=2, sort_keys=True)
    except Exception as e:
        pass


def settings_file():
    return os.getenv("HOME") + "/.fsel_history"


class FsApp:
    def __init__(self, root: str):
        self.root = root


class AppSelectRecent(FsApp):

    def run(self, recent_items):
        items_path = run_dialog(
            lambda screen_height, screen_width, cursor_y, cursor_x:
            ItemSelectionDialog(screen_height, screen_width, 0, 0, cursor_y, recent_items)
        )
        if items_path is None:
            sys.exit(1)
        return full_path(self.root, item_model.item_text(items_path[0]))


class AppSelectInPanes(FsApp):

    def run(self, dir: str, fs_model, root_history):
        fs_oracle = FsOracle(self.root, root_history)

        rel_path = os.path.relpath(dir, self.root)
        initial_path = rel_path.split('/') if rel_path != '.' else []
        folder_lists = ListBoxes(fs_model, fs_oracle, initial_path)
        if folder_lists.is_empty():
            sys.exit(2)

        items_path = run_dialog(
            lambda screen_height, screen_width, cursor_y, cursor_x:
            SelectPathDialog(folder_lists, screen_width, screen_height, width=1000, height=0, x=0, y=cursor_y)
        )
        if items_path is None:
            sys.exit(1)
        return fs_model.full_path(items_path)


def find_root(folder, settings: Dict) -> Tuple[str, str]:
    path = folder if not folder.endswith('/') else folder[:len(folder) - 1]

    while True:
        if path in settings:
            return path, folder
        if path == os.getenv('HOME') or path == '' or path.startswith('.'):
            return path, folder

        i = path.rfind('/')
        parent_path = path[:i]

        try:
            contents = os.listdir(path)
            if '.svn' in contents or '.git' in contents:
                settings[path] = {}
                return path
        except:  # folder may have been deleted
            folder = parent_path

        path = parent_path


class FsOracle(Oracle):
    def __init__(self, root: AnyStr, root_history: Dict):
        self.root = root
        self.root_history = root_history
        self.visit_history = {}

    def memorize(self, path: List[AnyStr], name: AnyStr, persistent: bool):
        storage = self.root_history if persistent else self.visit_history
        storage[self.string_path(path)] = name

    def recall_chosen_name(self, path):
        string_path = self.string_path(path)
        return self.visit_history.get(string_path) or \
               self.root_history.get(string_path)

    def recall_choice(self, path, items) -> int:
        string_path = self.string_path(path)
        return FsOracle.recall_choice_in(self.visit_history, string_path, items) or \
               FsOracle.recall_choice_in(self.root_history, string_path, items)

    @staticmethod
    def recall_choice_in(storage, path, items) -> int:
        if path in storage:
            last_name = storage[path]
            if last_name is not None:
                return item_model.index_of_item_text(last_name, items)

    @staticmethod
    def string_path(path):
        return '/'.join(path)


if __name__ == "__main__":
    if sys.stdin.isatty():
        path_args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
        target_is_file = '-f' in sys.argv[1:]
        target_is_executable = '-x' in sys.argv[1:]
        if target_is_file:
            field_for_recent = 'recent-executables' if target_is_executable else 'recent-files'
        else:
            field_for_recent = 'recent-folders'

        settings = load_settings()
        folder = os.getenv('PWD') if len(path_args) != 1 else path_args[0]
        root, folder = find_root(folder, settings)
        settings_for_root = field_or_else(settings, root, {})
        recent = field_or_else(settings_for_root, field_for_recent, [])

        if '-e' in sys.argv[1:]:
            if len(recent) == 0:
                sys.exit(2)

            # makes little sense to cd to the current directory...
            if recent[0] == os.path.relpath(os.environ["PWD"], root) and len(recent) > 1:  # PWD for logical path
                recent[0], recent[1] = recent[1], recent[0]

            app = AppSelectRecent(root)
            path = app.run([(name, False) for name in recent])
        else:
            app = AppSelectInPanes(root)
            lister = FsListFiles(app.root, target_is_file, target_is_executable)
            path = app.run(folder, FsModel(root, lister), root_history = field_or_else(settings_for_root, 'history', {}))

        if path is None:
            sys.exit(1)

        rel_path_from_root = os.path.relpath(path, start=app.root)
        update_recents(recent, rel_path_from_root)
        save_settings(settings)
        ret_rel_path = '-r' in sys.argv[1:]
        ret_rel_path_from_root = '-R' in sys.argv[1:]

        if ret_rel_path:
            res = os.path.relpath(path)
        elif ret_rel_path_from_root:
            res = rel_path_from_root
        else:
            res = path

        print(res)
