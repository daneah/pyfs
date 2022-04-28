import json
from typing import Literal, Generator

from pyfs import exceptions
from pyfs.inode import DirectoryNode, FileNode, INode, FileLike


class FileSystem:
    """
    The entry point to the in-memory file system.
    A file system starts with only the empty root directory ("/").
    The system maintains an adjacency map of inodes to keep track of directory and file locations.
    The current working directory is stored as a prefix path for indexing into the adjacency map.
    """

    PARENT_DIR_NAME = ".."
    THIS_DIR_NAME = "."
    PATH_SEPARATOR = "/"

    __slots__ = ["_current", "_path_to_current", "_root"]

    def __init__(self) -> None:
        root_inode = DirectoryNode()
        self._current = self._root = root_inode
        self._path_to_current: list[tuple[str, DirectoryNode]] = [("", root_inode)]

    def cd(self, name: str | Literal[".."] | Literal["."] | None = None) -> None:
        """Change the current working directory."""

        # cd with no arguments goes to "/"
        if not name:
            self._current = self._root
            self._path_to_current = [("", self._root)]
            return

        node = self._get_node_or_fail(name)
        if not isinstance(node, DirectoryNode):
            raise exceptions.NotADirectory(name)

        # Record-keeping for the prefix path
        self._path_to_current = self._resolve_path(name)
        self._current = self._path_to_current[-1][1]

    def create_file(self, name: str) -> FileNode:
        """Create an empty child file in the current working directory."""

        self._fail_if_node_exists(name)
        *parent_dirs, requested = name.split(self.PATH_SEPARATOR)
        parent_path = self.PATH_SEPARATOR.join(parent_dirs)
        parent_node = self._get_directory_or_fail(parent_path)
        file_node = FileNode()
        parent_node.add_child(requested, file_node)
        return file_node

    def cwd(self) -> str:
        """Get the current working directory path, relative to the root directory."""

        return self.PATH_SEPARATOR.join(ref[0] for ref in self._path_to_current) or "/"

    def find(self, name: str, relative_to: str | None = None) -> list[str]:
        """Find all files and directories with the given name under the current working directory."""

        starting_node = self._get_node_or_fail(relative_to) if relative_to else self._current

        # Depth-first search to traverse the entire directory tree
        found_paths = []
        adjacency_map = {}
        visited: set[tuple[str, FileLike]] = {("", starting_node)}
        nodes: list[tuple[str, FileLike]] = [("", starting_node)]
        while nodes:
            node = nodes.pop()
            file_name, node_obj = node[0], node[1]
            if isinstance(node_obj, DirectoryNode):
                for child in node_obj:
                    if child not in visited:
                        visited.add(child)
                        nodes.append(child)
                        adjacency_map[child] = node

        # Limit to nodes that match the requested name
        matches = [key for key, value in adjacency_map.items() if key[0] == name]

        # Coalesce the path between the node and the root
        for match in matches:
            path = [match[0]]
            parent = adjacency_map[match]
            while parent in adjacency_map:
                path.insert(0, parent[0])
                parent = adjacency_map[parent]
            path.insert(0, parent[0])
            if relative_to:
                path.insert(0, relative_to)
            found_paths.append("".join(self.PATH_SEPARATOR.join(part for part in path if part)))
        return found_paths

    def ls(self, name: str | None = None, *, show_details: bool = False) -> list[str]:
        """List the contents of the current working directory."""

        node = self._get_directory_or_fail(name) if name else self._current
        if show_details:
            details = []

            for child in node:
                child_name, child_node = child[0], child[1]
                # A fairly abitrary choice of output format here (JSON)
                # Would want to decouple and add a formatting aspect to the design to improve
                details.append(
                    json.dumps(
                        {
                            "name": child_name,
                            "ctime": child_node.ctime.strftime("%b %d %Y %H:%M:%S"),
                            "mtime": child_node.mtime.strftime("%b %d %Y %H:%M:%S"),
                            "atime": child_node.atime.strftime("%b %d %Y %H:%M:%S"),
                            "links": child_node.links,
                        }
                    )
                )
            return details

        return [child[0] for child in node]

    def ln(self, target: str, dest: str) -> FileLike:
        """Create a hard link to an existing node with a file in the current working directory."""

        target_node = self._get_node_or_fail(target)
        *dest_parent_dirs, dest_requested = dest.split(self.PATH_SEPARATOR)
        dest_parent_path = self.PATH_SEPARATOR.join(dest_parent_dirs)
        dest_parent_node = self._get_directory_or_fail(dest_parent_path)
        target_node.links += 1
        return dest_parent_node.add_child(dest_requested, target_node)

    def mkdir(self, name: str, *, create_intermediates: bool = False) -> DirectoryNode:
        """Make a new child directory in the current working directory."""

        self._fail_if_node_exists(name)
        *parent_dirs, requested_dir = name.split(self.PATH_SEPARATOR)
        parent_path = self.PATH_SEPARATOR.join(parent_dirs)
        if create_intermediates:
            self._create_tree(parent_path)
        parent_node = self._get_directory_or_fail(parent_path)
        node = DirectoryNode(parent=parent_node)
        parent_node.add_child(requested_dir, node)
        return node

    def mv(self, old_name: str, new_name: str) -> FileLike:
        """Move (rename) a file or directory in the current working directory."""

        node = self._get_node_or_fail(old_name)
        try:
            self._get_node_or_fail(new_name)
        except exceptions.NoSuchFileOrDirectory:
            pass

        *old_parent_dirs, old_requested = old_name.split(self.PATH_SEPARATOR)
        old_parent_path = self.PATH_SEPARATOR.join(old_parent_dirs)
        old_parent_node = self._get_directory_or_fail(old_parent_path)

        *new_parent_dirs, new_requested = new_name.split(self.PATH_SEPARATOR)
        new_parent_path = self.PATH_SEPARATOR.join(new_parent_dirs)
        new_parent_node = self._get_directory_or_fail(new_parent_path)

        # Don't overwrite a file with itself
        if (
            self._resolve_path(new_parent_path) == self._resolve_path(old_parent_path)
            and new_requested == old_requested
        ):
            return node

        new_parent_node.add_child(new_requested, node)
        old_parent_node.delete_child(old_requested)
        return node

    def read_file(self, name: str, *, stream: bool = False) -> str | Generator[str, None, None]:
        """Read the contents of a child file in the current working directory."""

        node = self._get_node_or_fail(name)
        if isinstance(node, DirectoryNode):
            raise exceptions.IsADirectory(name)

        return node.stream_contents() if stream else node.read_contents()

    def rm(self, name: str, *, recursive: bool = False) -> INode:
        """Remove a child directory from the current working directory."""

        node = self._get_node_or_fail(name)
        if isinstance(node, DirectoryNode) and not recursive:
            raise exceptions.IsADirectory(name)

        *parent_dirs, requested = name.split(self.PATH_SEPARATOR)
        parent_path = self.PATH_SEPARATOR.join(parent_dirs)
        parent_node = self._get_directory_or_fail(parent_path)

        node.links -= 1
        return parent_node.delete_child(requested)

    def touch(self, name: str) -> FileLike:
        """Make an empty child file in the current working directory."""

        if match := self._get_node(name):
            return match

        *parent_dirs, requested = name.split(self.PATH_SEPARATOR)
        parent_path = self.PATH_SEPARATOR.join(parent_dirs)
        parent_node = self._get_directory_or_fail(parent_path)
        return parent_node.add_child(requested, FileNode())

    def write_file(self, name: str, contents: str) -> FileNode:
        """
        Write contents to a child file in the current working directory.
        The file is created if it doesn't exist.
        """

        if isinstance(match := self._get_node(name), DirectoryNode):
            raise exceptions.IsADirectory(name)

        file = match or self.create_file(name)
        file.write_contents(contents)
        return file

    def _get_directory_or_fail(self, name: str) -> DirectoryNode:
        if not isinstance(node := self._get_node_or_fail(name), DirectoryNode):
            raise exceptions.NotADirectory(name)
        return node

    def _fail_if_node_exists(self, name: str) -> None:
        if self._get_node(name):
            raise exceptions.FileExists(name)

    def _get_node_or_fail(self, name: str) -> FileLike:
        if (node := self._get_node(name)) is None:
            raise exceptions.NoSuchFileOrDirectory(name)
        return node

    def _resolve_path(self, name: str) -> list[tuple[str, DirectoryNode]]:
        if name == "":
            return self._path_to_current

        is_root_relative = name.startswith(self.PATH_SEPARATOR)
        name = name[1:] if is_root_relative else name
        parts = name.split(self.PATH_SEPARATOR)

        node: DirectoryNode = self._root if is_root_relative else self._current
        path: list[tuple[str, DirectoryNode]] = [("", self._root)] if is_root_relative else self._path_to_current

        # Treat path as a stack as the parts get parsed
        for i, part in enumerate(parts):
            next_node = node.find_child(part)
            if next_node is None:
                raise exceptions.NoSuchFileOrDirectory(name)

            if isinstance(next_node, DirectoryNode):
                node = next_node

                if part == self.PARENT_DIR_NAME:
                    if len(path) > 1:
                        path.pop()
                elif part != self.THIS_DIR_NAME:
                    path.append((part, node))
        return path

    def _create_tree(self, name: str) -> None:
        is_root_relative = name.startswith(self.PATH_SEPARATOR)
        name = name[1:] if is_root_relative else name
        parts = name.split(self.PATH_SEPARATOR)

        node: FileLike = self._root if is_root_relative else self._current
        for name in parts:
            if isinstance(node, FileNode):
                raise exceptions.FileExists(name)
            existing_node = node.find_child(name)
            node = existing_node or node.add_child(name, DirectoryNode(parent=node))

    def _get_node(self, name: str | None = None) -> FileLike | None:
        if not name:
            return self._current

        is_root_relative = name.startswith(self.PATH_SEPARATOR)
        name = name[1:] if is_root_relative else name
        parts = name.split(self.PATH_SEPARATOR)

        node: FileLike | None = self._root if is_root_relative else self._current

        for part in parts:
            if node and isinstance(node, DirectoryNode):
                node = node.find_child(part)

        return node
