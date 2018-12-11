import os
from abc import ABC, abstractmethod
from threading import Lock
from pathlib import Path

from typing import Dict, List, Tuple


class Repository(ABC):
    def __init__(self, path: str):
        """
        Init the Git Repository.

        :param str path: path to the repository
        """
        self.path = Path(path)
        self.project_name = self.path.name
        self.main_branch = None
        self.lock = Lock()

    @abstractmethod
    def _discover_main_branch(self, repo):
        pass

    @abstractmethod
    def get_head(self):
        pass

    @abstractmethod
    def get_list_commits(self):
        pass

    @abstractmethod
    def _get_all_commits(self):
        pass

    @abstractmethod
    def get_commit(self, commit_id: str):
        pass

    @abstractmethod
    def checkout(self, _hash: str):
        pass

    @abstractmethod
    def _delete_tmp_branch(self):
        pass

    def files(self) -> List[str]:
        """
        Obtain the list of the files (excluding .git directory).

        :return: List[str], the list of the files
        """
        _all = []
        for path, subdirs, files in os.walk(str(self.path)):
            if '.git' in path:
                continue
            for name in files:
                _all.append(os.path.join(path, name))
        return _all

    @abstractmethod
    def reset(self):
        pass

    def total_commits(self):
        """
        Calculate total number of commits.

        :return: the total number of commits
        """
        return len(self.get_list_commits())

    @abstractmethod
    def get_commit_from_tag(self, tag: str):
        pass

    def parse_diff(self, diff: str) -> Dict[str, List[Tuple[int, str]]]:
        """
        Given a diff, returns a dictionary with the added and deleted lines.
        The dictionary has 2 keys: "added" and "deleted", each containing the
        corresponding added or deleted lines. For both keys, the value is a list
        of Tuple (int, str), corresponding to (number of line in the file, actual line).


        :param str diff: diff of the commit
        :return: Dictionary
        """
        lines = diff.split('\n')
        modified_lines = {'added': [], 'deleted': []}

        count_deletions = 0
        count_additions = 0

        for line in lines:
            line = line.rstrip()
            count_deletions += 1
            count_additions += 1

            if line.startswith('@@'):
                count_deletions, count_additions = self._get_line_numbers(line)

            if line.startswith('-'):
                modified_lines['deleted'].append((count_deletions, line[1:]))
                count_additions -= 1

            if line.startswith('+'):
                modified_lines['added'].append((count_additions, line[1:]))
                count_deletions -= 1

        return modified_lines

    def _get_line_numbers(self, line):
        token = line.split(" ")
        numbers_old_file = token[1]
        numbers_new_file = token[2]
        delete_line_number = int(numbers_old_file.split(",")[0].replace("-", "")) - 1
        additions_line_number = int(numbers_new_file.split(",")[0]) - 1
        return delete_line_number, additions_line_number

    @abstractmethod
    def get_commits_last_modified_lines(self, commit, modification):
        pass

    def _useless_line(self, line: str):
        # this covers comments in Java and Python, as well as empty lines. More have to be added!
        return line.startswith('//') or line.startswith('#') or line.startswith("/*") or \
               line.startswith("'''") or line.startswith('"""') or line == '' or line.startswith("*")