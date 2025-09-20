import os
import sys
from typing import List, AnyStr, Sequence

from fsel.lib.list_item import ListItem
from fsel.lib.list_item_info_service import ListItemInfoService


class FsListFiles:
    def __init__(self, root: AnyStr, select_files: bool, executables: bool, dot_files):
        self.root = root
        self.select_files = select_files
        self.executables = executables
        self.dot_files = dot_files

    def __call__(self, p: Sequence[str]) -> Sequence[ListItem]:
        """ Each item is a tuple; last element of tuple is int with item attributes (same as in st_mode) """
        return self.list_folders(p) + self.list_files(p)

    def list_folders(self, path: Sequence[str]) -> List[ListItem]:
        full_fs_path = os.path.join(self.root, *path)
        if full_fs_path == '':
            sys.exit(1)
        try:
            result = []
            # see DirEntry
            for entry in os.scandir(full_fs_path):
                if entry.is_dir() and not entry.name.startswith('.'):
                    st_mode = entry.stat().st_mode
                    entry_path = os.path.join(full_fs_path, entry.name)
                    description = self.get_description(entry_path)
                    
                    # Set flags based on attributes
                    flags = st_mode | ListItemInfoService.FLAG_DIRECTORY
                    if entry.is_symlink():
                        flags |= ListItemInfoService.FLAG_ITALIC
                    if self.is_deleted(entry_path):
                        flags |= ListItemInfoService.FLAG_STRIKE_THRU
                        
                    result.append(
                        ListItem(
                            name=entry.name,
                            attrs=flags,
                            description=description,
                        )
                    )
            return sorted(result, key=lambda e: e.name)
        except PermissionError:
            return []

    def get_description(self, path: str):
        """Get the description from the 'user.description' extended attribute"""
        try:
            return os.getxattr(path, 'user.description').decode('utf-8')
        except (OSError, AttributeError):
            return None
            
    def is_deleted(self, path: str):
        """Check if the 'user.deleted' extended attribute exists"""
        try:
            os.getxattr(path, 'user.deleted')
            return True
        except (OSError, AttributeError):
            return False

    def list_files(self, p: Sequence[str]) -> List[ListItem]:
        if not self.select_files:
            return []
        full_fs_path = os.path.join(self.root, *p)
        try:
            name: List[str] = os.listdir(full_fs_path)
            return [ListItem(name=entry, attrs=0, description=None) for entry in sorted(name) if self.is_suitable_file(full_fs_path, entry)]
        except PermissionError:
            return []

    def is_suitable_file(self, folder, name):
        return (self.dot_files or not name.startswith('.')) and self.is_suitable_file_path(folder + '/' + name)

    def is_suitable_file_path(self, path):
        is_file = os.path.isfile(path)
        if not is_file: return False
        if self.executables: return os.access(path, os.X_OK)
        return True
