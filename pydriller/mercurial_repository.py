import hglib
from typing import List

from pydriller.domain.commit_mercurial import CommitMercurial
from pydriller.repository import Repository
from hglib import client


class MercurialRepository(Repository):
    def __init__(self, path: str):
        """
        Init the Git Repository.

        :param str path: path to the repository
        """
        super().__init__(path)
        # client = hglib.open(path)

    def _open_mercurial(self):
        client = hglib.open(self.path)
        if self.main_branch == None:
            self._discover_main_branch(client)
        return client

    def _discover_main_branch(self, client):
        self.main_branch = client.tip().branch.decode('utf-8')

    def get_head(self):
        client = self._open_mercurial()
        return CommitMercurial(client.tip(), self.path, self.main_branch)

    def get_list_commits(self):
        return self._get_all_commits()

    def _get_all_commits(self) -> List[CommitMercurial]:
        client = self._open_mercurial()

        all_commits = []
        for commit in client.log():
            all_commits.append(self.get_commit_from_hglib(commit))
        return all_commits

    def get_commit(self, commit_id: str):
        client = self._open_mercurial()
        return CommitMercurial(client.log(commit_id), self.path, self.main_branch)

    def get_commit_from_hglib(self, commit):
        return CommitMercurial(commit, self.path, self.main_branch)

    def checkout(self, _hash: str):
        pass

    def _delete_tmp_branch(self):
        pass

    def reset(self):
        pass

    def total_commits(self):
        return len(self.get_list_commits())
        pass

    def get_commit_from_tag(self, tag: str):
        pass

    def get_commits_last_modified_lines(self, commit, modification):
        pass