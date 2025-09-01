import os
import sys
from typing import Tuple, Set, Dict

from fsel.logging import debug
from fsel.sdk import FsListFiles, run_dialog, ItemSelectionDialog, full_path, item_model, field_or_else, \
    ListBoxes, SelectPathDialog, PathOracle, AllSettingsFolder

RECENT_COUNT = 10


class FsApp:
    def __init__(self, root: str):
        self.root = root


class AppSelectRecent(FsApp):

    def run(self, recent_items: list[Tuple[str, int, str|None]]):
        exit_code, items_path = run_dialog(
            lambda screen_height, screen_width, cursor_y, cursor_x:
            ItemSelectionDialog(screen_height, screen_width, 0, 0, cursor_y, recent_items)
        )
        if items_path is None:
            sys.exit(1)
        return exit_code, full_path(self.root, item_model.item_file_name(items_path[0]))


class AppSelectInPanes(FsApp):

    def run(self, path: str, fs_lister, root_history: Dict, usage_stats: Dict):
        fs_oracle = PathOracle(root_history, usage_stats)

        rel_path = os.path.relpath(path, self.root)
        debug("AppSelectInPanes.run", path=path, rel_path=rel_path)
        initial_path = rel_path.split('/') if rel_path != '.' else []
        folder_lists = ListBoxes(fs_lister, fs_oracle, initial_path)
        if folder_lists.is_empty():
            sys.exit(2)

        exit_code, items_path = run_dialog(
            lambda screen_height, screen_width, cursor_y, cursor_x:
            SelectPathDialog(folder_lists, screen_width, screen_height, width=1000, height=0, x=0, y=cursor_y)
        )
        if items_path is None:
            sys.exit(1)
        return exit_code, self.full_path(items_path)

    def full_path(self, items_path):
        return os.path.join(self.root, *[item_model.item_file_name(i) for i in items_path])


def find_root(folder: str, roots: Set[str]) -> Tuple[str, str]:
    root_candidate = folder if not folder.endswith('/') else folder[:len(folder) - 1]

    while True:
        if root_candidate in roots:
            return root_candidate, folder
        if root_candidate == os.getenv('HOME') or root_candidate == '' or root_candidate.startswith('.'):
            return root_candidate, folder

        i = root_candidate.rfind('/')
        parent_path = root_candidate[:i]

        try:
            contents = os.listdir(root_candidate)
            if '.svn' in contents or '.git' in contents or '.arc' in contents:
                return root_candidate, folder
        except:  # folder may have been deleted
            folder = parent_path

        root_candidate = parent_path


def update_recents(recent, rel_path_from_root):
    if rel_path_from_root != '.':
        if rel_path_from_root in recent:
            recent.remove(rel_path_from_root)
        recent.insert(0, rel_path_from_root)
        del recent[RECENT_COUNT:]


def main():
    """
    Arguments: [-W] [-f] [-x] [-a] [-e] [selected folder] [displayed root]
    """
    path_args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    wd = os.getenv('PWD')
    folder = wd if len(path_args) != 1 else os.path.realpath(path_args[0])
    displayed_root = None if len(path_args) < 2 else os.path.realpath(path_args[1])

    search_root_from_work_dir = '-W' in sys.argv[1:]
    target_is_file = '-f' in sys.argv[1:]
    target_is_executable = '-x' in sys.argv[1:]
    show_dot_files = '-a' in sys.argv[1:]
    show_recent = '-e' in sys.argv[1:]
    if target_is_file:
        field_for_recent = 'recent-executables' if target_is_executable else 'recent-files'
    else:
        field_for_recent = 'recent-folders'
    all_settings = AllSettingsFolder(os.getenv("HOME") + "/.cache/fsel")
    if search_root_from_work_dir:
        root, _ = find_root(wd, all_settings.roots)
        rel_path = os.path.relpath(folder, root)
        if rel_path.startswith('..'):
            root, folder = find_root(folder, all_settings.roots)
    else:
        root, folder = find_root(folder, all_settings.roots)
    debug("main", root=root, folder=folder)
    settings_for_root = all_settings.load_settings(root)
    recent = field_or_else(settings_for_root, field_for_recent, [])

    if show_recent:
        if len(recent) == 0:
            sys.exit(2)

        # makes little sense to cd to the current directory...
        if recent[0] == os.path.relpath(os.environ["PWD"], root) and len(recent) > 1:  # PWD for logical path
            recent[0], recent[1] = recent[1], recent[0]

        app = AppSelectRecent(root)
        exit_code, path = app.run([(name, False, None) for name in recent])
    else:
        app = AppSelectInPanes(displayed_root or root)
        exit_code, path = app.run(
            folder,
            FsListFiles(app.root, target_is_file, target_is_executable, show_dot_files),
            root_history=field_or_else(settings_for_root, 'history', {}),
            usage_stats=field_or_else(settings_for_root, 'usage_stats', {})
        )

    if path is None:
        sys.exit(1)

    rel_path_from_root = os.path.relpath(path, start=app.root)
    update_recents(recent, rel_path_from_root)
    all_settings.save(settings_for_root, root)
    ret_rel_path = '-r' in sys.argv[1:]
    ret_rel_path_from_root = '-R' in sys.argv[1:]
    if ret_rel_path:
        res = os.path.relpath(path)
    elif ret_rel_path_from_root:
        res = rel_path_from_root
    else:
        res = path
    print(res)
    sys.exit(exit_code)


if __name__ == "__main__":
    if sys.stdin.isatty():
        main()
