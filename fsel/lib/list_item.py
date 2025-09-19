from dataclasses import dataclass
from typing import Optional


@dataclass
class ListItem:
    """Represents an item in a list box (file or folder)"""
    name: str
    attrs: int
    description: Optional[str] = None