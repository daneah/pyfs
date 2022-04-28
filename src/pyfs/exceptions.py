__all__ = [
    "NoSuchFileOrDirectory",
    "NotADirectory",
    "IsADirectory",
    "FileExists",
]


class PyFSError(Exception):
    """Base exception class for pyfs"""


class NoSuchFileOrDirectory(PyFSError):
    """Raised when a command runs against a file or directory that does not exist."""

    pass


class NotADirectory(PyFSError):
    """Raised when an operation that expects a directory gets a different file type."""

    pass


class IsADirectory(PyFSError):
    """Raised when an operation expects a regular file or requires permission to operate recursively."""

    pass


class FileExists(PyFSError):
    """Raised when an operation attempts to create a file with a name that already exists."""

    pass
