import hglib
from typing import List

from pydriller.domain.commit_mercurial import CommitMercurial
from pydriller.repository import Repository


class MercurialRepository(Repository):

    @property
    def client(self):
        return self._open_mercurial()

    def _open_mercurial(self):
        client = hglib.open(str(self.path))

        if self.main_branch is None:
            self._discover_main_branch(client)
        return client

    def _discover_main_branch(self, client):
        self.main_branch = client.tip().branch.decode('utf-8')

    def get_head(self):
        return CommitMercurial(self.client.tip(), self.client, self.path, self.main_branch)

    def get_list_commits(self):
        return self._get_all_commits()

    def _get_all_commits(self) -> List[CommitMercurial]:
        all_commits = []
        for commit in self.client.log():
            all_commits.append(self.get_commit_from_hglib(commit))
        return all_commits

    def get_commit(self, commit_id: str):
        return CommitMercurial(self.client.log(commit_id)[0], self.client, self.path, self.main_branch)

    def get_commit_from_hglib(self, commit):
        return CommitMercurial(commit, self.client, self.path, self.main_branch)

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