# Copyright 2018 Davide Spadini
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
from typing import List, Dict, Tuple, Set

from git import Git, Repo, GitCommandError, Commit as GitCommit

from pydriller.domain.commit import Commit, ModificationType, Modification
from pydriller.repository import Repository

logger = logging.getLogger(__name__)

NULL_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'


class GitRepository(Repository):
    @property
    def git(self):
        """
        GitPython object Git.

        :return: Git
        """
        return self._open_git()

    @property
    def repo(self):
        """
        GitPython object Repo.

        :return: Repo
        """
        return self._open_repository()

    def _open_git(self) -> Git:
        return Git(str(self.path))

    def _open_repository(self) -> Repo:
        repo = Repo(str(self.path))
        if self.main_branch is None:
            self._discover_main_branch(repo)
        return repo

    def _discover_main_branch(self, repo):
        self.main_branch = repo.active_branch.name

    def get_head(self) -> Commit:
        """
        Get the head commit.

        :return: Commit of the head commit
        """
        head_commit = self.repo.head.commit
        return Commit(head_commit, self.path, self.main_branch)

    def get_list_commits(self, branch: str = None) -> List[Commit]:
        """
        Return the list of all the commits in the repo.

        :return: List[Commit], the list of all the commits in the repo
        """
        return self._get_all_commits(branch)

    def _get_all_commits(self, branch: str = None) -> List[Commit]:
        all_commits = []
        for commit in self.repo.iter_commits(branch):
            all_commits.append(self.get_commit_from_gitpython(commit))
        return all_commits

    def get_commit(self, commit_id: str) -> Commit:
        """
        Get the specified commit.

        :param str commit_id: hash of the commit to analyze
        :return: Commit
        """
        return Commit(self.repo.commit(commit_id), self.path, self.main_branch)

    def get_commit_from_gitpython(self, commit: GitCommit) -> Commit:
        """
        Build a PyDriller commit object from a GitPython commit object.
        This is internal of PyDriller, I don't think users generally will need
        it.

        :param GitCommit commit: GitPython commit
        :return: Commit commit: PyDriller commit
        """
        return Commit(commit, self.path, self.main_branch)

    def checkout(self, _hash: str) -> None:
        """
        Checkout the repo at the speficied commit.
        BE CAREFUL: this will change the state of the repo, hence it should *not*
        be used with more than 1 thread.

        :param _hash: commit hash to checkout
        """
        with self.lock:
            self._delete_tmp_branch()
            self.git.checkout('-f', _hash, b='_PD')

    def _delete_tmp_branch(self) -> None:
        try:
            # we are already in _PD, so checkout the master branch before deleting it
            if self.repo.active_branch.name == '_PD':
                self.git.checkout('-f', self.main_branch)
            self.repo.delete_head('_PD', force=True)
        except GitCommandError:
            logger.debug("Branch _PD not found")

    def reset(self) -> None:
        """
        Reset the state of the repo, checking out the main branch and discarding
        local changes (-f option).

        """
        with self.lock:
            self.git.checkout('-f', self.main_branch)
            self._delete_tmp_branch()

    def get_commit_from_tag(self, tag: str) -> Commit:
        """
        Obtain the tagged commit.

        :param str tag: the tag
        :return: Commit commit: the commit the tag referred to
        """
        try:
            selected_tag = self.repo.tags[tag]
            return self.get_commit(selected_tag.commit.hexsha)
        except (IndexError, AttributeError):
            logger.debug('Tag {} not found'.format(tag))
            raise

    def get_commits_last_modified_lines(self, commit: Commit, modification: Modification = None) -> Set[str]:
        """
        Given the Commit object, returns the set of commits that last "touched" the lines
        that are modified in the files included in the commit. It applies SZZ.
        The algorithm works as follow: (for every file in the commit)

        1- obtain the diff

        2- obtain the list of deleted lines

        3- blame the file and obtain the commits were those lines were added

        Can also be passed as parameter a single Modification, in this case only this file
        will be analyzed.

        :param Commit commit: the commit to analyze
        :param Modification modification: single modification to analyze
        :return: the set containing all the bug inducing commits
        """
        buggy_commits = set()

        if modification is not None:
            modifications = [modification]
        else:
            modifications = commit.modifications

        for mod in modifications:
            path = mod.new_path
            if mod.change_type == ModificationType.RENAME or mod.change_type == ModificationType.DELETE:
                path = mod.old_path

            deleted_lines = self.parse_diff(mod.diff)['deleted']
            try:
                blame = self.git.blame(commit.hash + '^', '--', path).split('\n')
                for num_line, line in deleted_lines:
                    if not self._useless_line(line.strip()):
                        buggy_commit = blame[num_line - 1].split(' ')[0].replace('^', '')
                        buggy_commits.add(self.get_commit(buggy_commit).hash)
            except GitCommandError:
                logger.debug("Could not found file %s in commit %s. Probably a double rename!", mod.filename,
                             commit.hash)

        return buggy_commits
