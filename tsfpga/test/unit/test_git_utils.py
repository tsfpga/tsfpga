# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from pathlib import Path
import os
import unittest

import pytest

from tsfpga.git_utils import (check_that_git_commands_are_available,
                              find_git_files,
                              get_git_commit,
                              git_local_changes_are_present)
from tsfpga.system_utils import create_file, delete, run_command, system_is_windows


THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent


def test_this_file_is_listed_by_find_git_files_without_argument():
    git_files = find_git_files()
    assert THIS_FILE in git_files


def test_this_file_is_listed_by_find_git_files_with_argument():
    # Test with string as well as tuple
    git_files = find_git_files(file_endings_include="py")
    assert THIS_FILE in git_files
    git_files = find_git_files(file_endings_include=("py", ))
    assert THIS_FILE in git_files


def test_this_file_is_not_listed_by_find_git_files_with_bad_argument():
    git_files = find_git_files(file_endings_include="vhd")
    assert THIS_FILE not in git_files


def test_this_file_is_not_listed_by_find_git_files_with_file_endings_avoid():
    # Test with string as well as tuple
    git_files = find_git_files(file_endings_avoid="py")
    assert THIS_FILE not in git_files
    git_files = find_git_files(file_endings_avoid=("py", ))
    assert THIS_FILE not in git_files


def test_this_file_is_not_listed_by_find_git_files_with_exclude_directory():
    git_files = find_git_files(exclude_directories=[THIS_DIR])
    assert THIS_FILE not in git_files

    git_files = find_git_files(exclude_directories=[THIS_DIR.parent])
    assert THIS_FILE not in git_files

    git_files = find_git_files(exclude_directories=[THIS_DIR.parent, THIS_DIR])
    assert THIS_FILE not in git_files

    git_files = find_git_files(exclude_directories=[THIS_FILE])
    assert THIS_FILE not in git_files


def test_this_file_is_listed_by_find_git_files_with_bad_exclude_directory():
    git_files = find_git_files(exclude_directories=[THIS_DIR.parent / "apa"])
    assert THIS_FILE in git_files


def test_check_that_git_commands_are_available_with_current_cwd_should_pass():
    check_that_git_commands_are_available()


def test_check_that_git_commands_are_available_with_invalid_cwd_should_raise_exception():
    if system_is_windows():
        path_outside_of_repo = "c:/"
    else:
        path_outside_of_repo = "/"

    with pytest.raises(RuntimeError) as exception_info:
        check_that_git_commands_are_available(cwd=path_outside_of_repo)
    assert str(exception_info.value).startswith("Could not run git")


def test_get_git_commit_without_local_changes():
    if git_local_changes_are_present():
        assert False, "Must be run from clean repo (on CI server or locally)"
    assert len(get_git_commit()) == 16


class TestGitCommitWithLocalChanges(unittest.TestCase):

    _trash_file = "local_file_for_git_test.apa"
    _trash_file_path = THIS_DIR / _trash_file

    def setUp(self):
        check_that_git_commands_are_available(cwd=THIS_DIR)
        create_file(self._trash_file_path)
        run_command(["git", "add", self._trash_file], cwd=THIS_DIR)

    def tearDown(self):
        run_command(["git", "reset", self._trash_file], cwd=THIS_DIR)
        delete(self._trash_file_path)

    @staticmethod
    def test_get_git_commit_with_local_changes():
        assert get_git_commit().endswith(" (local changes present)")

    @staticmethod
    def test_get_git_commit_with_env_variable_and_local_changes():
        if "GIT_COMMIT" in os.environ:
            old_git_commit = os.environ["GIT_COMMIT"]
        else:
            old_git_commit = None

        os.environ["GIT_COMMIT"] = "54849b5a8152b07e0809b8f90fc24d54262cb4d6"
        assert get_git_commit() == os.environ["GIT_COMMIT"][0:16]

        if old_git_commit is None:
            del os.environ["GIT_COMMIT"]
        else:
            os.environ["GIT_COMMIT"] = old_git_commit
