# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import os
import unittest
from pathlib import Path

# Third party libraries
import pytest
from git import Actor, Repo

# First party libraries
from tsfpga import REPO_ROOT, TSFPGA_DOC
from tsfpga.git_utils import find_git_files, get_git_commit, git_commands_are_available
from tsfpga.system_utils import create_directory, create_file, system_is_windows

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent


def test_this_file_is_listed_by_find_git_files():
    git_files = find_git_files(directory=THIS_DIR, file_endings_include="py")
    assert THIS_FILE in git_files
    # Test with string as well as tuple
    git_files = find_git_files(directory=REPO_ROOT, file_endings_include="py")
    assert THIS_FILE in git_files
    git_files = find_git_files(directory=REPO_ROOT, file_endings_include=("py",))
    assert THIS_FILE in git_files


def test_this_file_is_not_listed_by_find_git_files_with_bad_argument():
    git_files = find_git_files(directory=TSFPGA_DOC)
    assert THIS_FILE not in git_files
    git_files = find_git_files(directory=REPO_ROOT, file_endings_include="vhd")
    assert THIS_FILE not in git_files


def test_this_file_is_not_listed_by_find_git_files_with_file_endings_avoid():
    # Test with string as well as tuple
    git_files = find_git_files(directory=REPO_ROOT, file_endings_avoid="py")
    assert THIS_FILE not in git_files
    git_files = find_git_files(directory=REPO_ROOT, file_endings_avoid=("py",))
    assert THIS_FILE not in git_files


def test_this_file_is_not_listed_by_find_git_files_with_exclude_directory():
    git_files = find_git_files(directory=REPO_ROOT, exclude_directories=[THIS_DIR])
    assert THIS_FILE not in git_files

    git_files = find_git_files(directory=REPO_ROOT, exclude_directories=[THIS_DIR.parent])
    assert THIS_FILE not in git_files

    git_files = find_git_files(directory=REPO_ROOT, exclude_directories=[THIS_DIR.parent, THIS_DIR])
    assert THIS_FILE not in git_files

    git_files = find_git_files(directory=REPO_ROOT, exclude_directories=[THIS_FILE])
    assert THIS_FILE not in git_files


def test_this_file_is_listed_by_find_git_files_with_bad_exclude_directory():
    git_files = find_git_files(directory=REPO_ROOT, exclude_directories=[THIS_DIR.parent / "apa"])
    assert THIS_FILE in git_files


def test_git_commands_are_available_should_pass():
    assert git_commands_are_available(directory=THIS_DIR)
    assert git_commands_are_available(directory=REPO_ROOT)


def test_git_commands_are_available_with_invalid_directory_should_fail():
    if system_is_windows():
        path_outside_of_repo = "c:/"
    else:
        path_outside_of_repo = "/"

    assert not git_commands_are_available(directory=path_outside_of_repo)


@pytest.mark.usefixtures("fixture_tmp_path")
class TestGitCommitWithLocalChanges(unittest.TestCase):
    tmp_path = None

    _local_changes_present = " (local changes present)"

    def setUp(self):
        self.repo_path = self.tmp_path / "my_repo"
        self.repo = Repo.init(self.repo_path)
        self.actor = Actor("A name", "an@email.com")

        initial_file = create_file(self.repo_path / "initial_commit_file.txt")
        self.repo.index.add(str(initial_file))
        self.repo.index.commit("Initial commit", author=self.actor, committer=self.actor)

        trash_file = create_file(self.repo_path / "local_file_for_git_test.apa")
        self.repo.index.add(str(trash_file))

    def test_get_git_commit_with_local_changes(self):
        assert get_git_commit(directory=self.repo_path).endswith(self._local_changes_present)

    def test_get_git_commit_with_env_variable_and_local_changes(self):
        if "GIT_COMMIT" in os.environ:
            old_env = os.environ["GIT_COMMIT"]
        else:
            old_env = None

        os.environ["GIT_COMMIT"] = "54849b5a8152b07e0809b8f90fc24d54262cb4d6"
        assert (
            get_git_commit(directory=self.repo_path)
            == f"{os.environ['GIT_COMMIT'][0:16]}{self._local_changes_present}"
        )

        if old_env is None:
            del os.environ["GIT_COMMIT"]
        else:
            os.environ["GIT_COMMIT"] = old_env

    def test_get_git_commit_without_local_changes(self):
        self.repo.index.commit("Trash commit", author=self.actor, committer=self.actor)
        assert not get_git_commit(directory=self.repo_path).endswith(self._local_changes_present)

    def test_get_git_commit_from_child_directory(self):
        child_directory = create_directory(self.repo_path / "child_directory")
        assert get_git_commit(directory=child_directory).endswith(self._local_changes_present)
