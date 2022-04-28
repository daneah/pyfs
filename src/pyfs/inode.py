from __future__ import annotations

from datetime import datetime
from typing import Generator


class INode:
    __slots__ = ["ctime", "mtime", "atime", "links"]

    def __init__(self):
        self.ctime = self.mtime = self.atime = datetime.now()
        self.links = 1

    def mark_accessed(self):
        self.atime = datetime.now()

    def mark_modified(self):
        self.mtime = datetime.now()


class DirectoryNode(INode):
    THIS_DIRECTORY = "."
    PARENT_DIRECTORY = ".."

    __slots__ = [
        "_meta",
        "_children",
    ]

    def __init__(self, parent: DirectoryNode | None = None):
        super().__init__()
        self._meta = {
            self.THIS_DIRECTORY: self,
            self.PARENT_DIRECTORY: parent or self,
        }
        self._children: dict[str, FileLike] = {}

    def find_child(self, name: str) -> FileLike | None:
        """Return a child or meta node, should one exist"""

        self.mark_accessed()
        return self._children.get(name) or self._meta.get(name)

    # Would've like to use a stricter TypeVar here to ensure the input type and output type coalesce.
    # Mypy was fighting me on it with an error I couldn't grok.
    def add_child(self, name: str, node: FileLike) -> FileLike:
        """Add a node under this directory node with the given file name"""

        self.mark_modified()
        self._children[name] = node
        return node

    def delete_child(self, name: str) -> FileLike:
        """
        Remove the file with the given name under this directory node.
        The inode may or may not be removed; remaining hard links may keep it around, as an example.
        """

        self.mark_modified()
        return self._children.pop(name)

    def __iter__(self) -> Generator[tuple[str, FileLike], None, None]:
        self.mark_accessed()
        yield from self._children.items()

    def __repr__(self):
        return f"<Directory>"


class FileNode(INode):
    __slots__ = ["_contents"]

    def __init__(self):
        super().__init__()
        self._contents = ""

    def write_contents(self, contents: str) -> FileNode:
        """Write the specified contents to this file node."""

        self.mark_modified()
        self._contents = contents
        return self

    def read_contents(self) -> str:
        """Read the contents of this file node."""

        self.mark_accessed()
        return self._contents

    def stream_contents(self) -> Generator[str, None, None]:
        self.mark_accessed()
        yield from self._contents

    def __repr__(self):
        return f"<File>"


FileLike = FileNode | DirectoryNode
