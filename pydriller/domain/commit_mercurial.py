from datetime import datetime
from enum import Enum
from pathlib import Path

import lizard
from hglib import client
from typing import Set, List, Dict

from pydriller.domain.developer import Developer


class ModificationType(Enum):
    MODIFY = 1,
    ADD = 2,
    REMOVED = 3,
    CLEAN = 4,
    MISSING = 5,
    UNTRACKED = 6,
    IGNORED = 7


class Method:
    def __init__(self, func):
        """
        Initialize a method object. This is calculated using Lizard: it parses
        the source code of all the modifications in a commit, extracting information
        of the methods contained in the file (if the file is a source code written
        in one of the supported programming languages).
        """

        self.name = func.name
        self.long_name = func.long_name
        self.filename = func.filename
        self.nloc = func.nloc
        self.complexity = func.cyclomatic_complexity
        self.token_count = func.token_count
        self.parameters = func.parameters
        self.start_line = func.start_line
        self.end_line = func.end_line
        self.fan_in = func.fan_in
        self.fan_out = func.fan_out
        self.general_fan_out = func.general_fan_out
        self.length = func.length
        self.top_nesting_level = func.top_nesting_level


class Modification:
    def __init__(self, old_path: str, new_path: str,
                 change_type: ModificationType,
                 diff_and_sc: Dict[str, str]):
        """
        Initialize a modification. A modification carries on information regarding
        the changed file. Normally, you shouldn't initialize a new one.
        """
        self._old_path = Path(old_path) if old_path is not None else None
        self._new_path = Path(new_path) if new_path is not None else None
        self.change_type = change_type
        self.diff = diff_and_sc['diff']
        self.source_code = diff_and_sc['source_code']

        self._nloc = None
        self._complexity = None
        self._token_count = None
        self._function_list = []

    @property
    def added(self) -> int:
        """
        Return the total number of added lines in the file.

        :return: int lines_added
        """
        added = 0
        for line in self.diff.replace('\r', '').split("\n"):
            if line.startswith('+') and not line.startswith('+++'):
                added += 1
        return added

    @property
    def removed(self):
        """
        Return the total number of deleted lines in the file.

        :return: int lines_deleted
        """
        removed = 0
        for line in self.diff.replace('\r', '').split("\n"):
            if line.startswith('-') and not line.startswith('---'):
                removed += 1
        return removed

    @property
    def old_path(self):
        """
        Old path of the file. Can be None if the file is added.

        :return: str old_path
        """
        if self._old_path:
            return str(self._old_path)
        return self._old_path

    @property
    def new_path(self):
        """
        New path of the file. Can be None if the file is deleted.

        :return: str new_path
        """
        if self._new_path:
            return str(self._new_path)
        return self._new_path

    @property
    def filename(self) -> str:
        """
        Return the filename. Given a path-like-string (e.g.
        "/Users/dspadini/pydriller/myfile.py") returns only the filename
        (e.g. "myfile.py")

        :return: str filename
        """
        if self._new_path is not None and str(self._new_path) != "/dev/null":
            path = self._new_path
        else:
            path = self._old_path

        return path.name

    @property
    def nloc(self) -> int:
        """
        Calculate the LOC of the file.

        :return: LOC of the file
        """
        self._calculate_metrics()
        return self._nloc

    @property
    def complexity(self) -> int:
        """
        Calculate the Cyclomatic Complexity of the file.

        :return: Cyclomatic Complexity of the file
        """
        self._calculate_metrics()
        return self._complexity

    @property
    def token_count(self) -> int:
        """
        Calculate the token count of functions.

        :return: token count
        """
        self._calculate_metrics()
        return self._token_count

    @property
    def methods(self) -> List[Method]:
        """
        Return the list of methods in the file. Every method
        contains various information like complexity, loc, name,
        number of parameters, etc.

        :return: list of methods
        """
        self._calculate_metrics()
        return self._function_list

    def _calculate_metrics(self):
        if self.source_code and self._nloc is None:
            l = lizard.analyze_file.analyze_source_code(self.filename, self.source_code)

            self._nloc = l.nloc
            self._complexity = l.CCN
            self._token_count = l.token_count

            for func in l.function_list:
                self._function_list.append(Method(func))

    def __eq__(self, other):
        if not isinstance(other, Modification):
            return NotImplemented
        elif self is other:
            return True
        else:
            return self.__dict__ == other.__dict__

    def __str__(self):
        return (
                'MODIFICATION\n' +
                'Old Path: {}\n'.format(self.old_path) +
                'New Path: {}\n'.format(self.new_path) +
                'Type: {}\n'.format(self.change_type.name) +
                'Diff: {}\n'.format(self.diff) +
                'Source code: {}\n'.format(self.source_code)
        )

class CommitMercurial():
    def __init__(self, commit: client.revision, client: client, path: str, main_branch: str) -> None:
        """
        Create a commit object.
        """
        self._client = client
        self._c_object = commit
        self._path = path
        self._main_branch = main_branch

    @property
    def changeset(self) -> int:
        return self._c_object[0]

    @property
    def hash(self) -> str:
        return self._c_object[1]

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
        return self._c_object[5]

    @property
    def parents(self) -> List[str]:
        pass

    @property
    def merge(self) -> bool:
        pass

    @property
    def modifications(self):
        commit = self._c_object

        files_changed = self._client.status(change=commit.node)
        for mod_type, filename in files_changed:
            print(mod_type, filename)

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
                'Author date: {}'.format(self.author_date.strftime("%Y-%m-%d %H:%M:%S")) + '\n'
                'Message: {}'.format(self.msg) + '\n'
                'Parent: {}'.format("\n".join(map(str, self.parents))) + '\n'
                'Merge: {}'.format(self.merge) + '\n'
                'Modifications: \n{}'.format("\n".join(map(str, self.modifications))) + '\n'
                'Branches: \n{}'.format("\n".join(map(str, self.branches))) + '\n'
                'In main branch: {}'.format(self.in_main_branch)
                )