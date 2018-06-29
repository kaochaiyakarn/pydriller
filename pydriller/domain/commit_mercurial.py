from datetime import datetime

from hglib import client
from typing import Set, List

from pydriller.domain.developer import Developer


class CommitMercurial():
    def __init__(self, commit: client.revision, path: str, main_branch: str) -> None:
        """
        Create a commit object.
        """
        self._c_object = commit
        self._path = path
        self._main_branch = main_branch

    @property
    def hash(self) -> str:
        return self._c_object[1]

    @property
    def changeset(self) -> int:
        return self._c_object[0]

    @property
    def author(self) -> Developer:
        name, email = self._format_developer(self._c_object[4].decode('utf-8'))
        return Developer(name, email)

    def _format_developer(self, authorname_email):
        name, email = authorname_email.split(' <')
        email = email.split('>')[0]
        return name, email

    @property
    def author_date(self) -> datetime:
        return self._c_object[6]

    @property
    def msg(self) -> str:
        return self._c_object[6]

    @property
    def parents(self) -> List[str]:
        pass

    @property
    def merge(self) -> bool:
        pass

    @property
    def modifications(self):
        pass

    @property
    def in_main_branch(self) -> bool:
        pass

    @property
    def branches(self) -> Set[str]:
        pass

    # def _from_change_to_modification_type(self, d: Diff):
    #     if d.new_file:
    #         return ModificationType.ADD
    #     elif d.deleted_file:
    #         return ModificationType.DELETE
    #     elif d.renamed_file:
    #         return ModificationType.RENAME
    #     elif d.a_blob and d.b_blob and d.a_blob != d.b_blob:
    #         return ModificationType.MODIFY

    # def __eq__(self, other):
    #     if not isinstance(other, Commit):
    #         return NotImplemented
    #     elif self is other:
    #         return True
    #     else:
    #         return self.__dict__ == other.__dict__

    def __str__(self):
        return ('Hash: {}'.format(self.hash) + '\n'
                'Author: {}'.format(self.author.name) + '\n'
                'Author email: {}'.format(self.author.email) + '\n'
                'Committer: {}'.format(self.committer.name) + '\n'
                'Committer email: {}'.format(self.committer.email) + '\n'
                'Author date: {}'.format(self.author_date.strftime("%Y-%m-%d %H:%M:%S")) + '\n'
                'Committer date: {}'.format(self.committer_date.strftime("%Y-%m-%d %H:%M:%S")) + '\n'
                'Message: {}'.format(self.msg) + '\n'
                'Parent: {}'.format("\n".join(map(str, self.parents))) + '\n'
                'Merge: {}'.format(self.merge) + '\n'
                'Modifications: \n{}'.format("\n".join(map(str, self.modifications))) + '\n'
                'Branches: \n{}'.format("\n".join(map(str, self.branches))) + '\n'
                'In main branch: {}'.format(self.in_main_branch)
                )