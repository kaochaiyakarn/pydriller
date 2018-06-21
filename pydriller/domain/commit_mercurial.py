from hglib import client

class CommitMercurial():
    def __init__(self, commit: client.revision, path: str, main_branch: str) -> None:
        """
        Create a commit object.
        """
        self._c_object = commit
        self._path = path
        self._main_branch = main_branch