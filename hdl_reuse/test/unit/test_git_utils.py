from os.path import abspath, dirname
import pytest
import unittest

from hdl_reuse.git_utils import *  # pylint: disable=wildcard-import,unused-wildcard-import
import hdl_reuse
from hdl_reuse.system_utils import create_file, delete
from hdl_reuse.system_utils import run_command


THIS_FILE = abspath(__file__)
THIS_DIR = dirname(__file__)


def test_this_file_is_listed_by_find_git_files_without_argument():
    git_files = find_git_files()
    assert THIS_FILE in git_files


def test_this_file_is_listed_by_find_git_files_with_argument():
    git_files = find_git_files(file_ending="py")
    assert THIS_FILE in git_files


def test_this_file_is_not_listed_by_find_git_files_with_bad_argument():
    git_files = find_git_files(file_ending="vhd")
    assert THIS_FILE not in git_files


def test_check_that_git_commands_are_available_with_current_cwd_should_pass():
    check_that_git_commands_are_available()


def test_check_that_git_commands_are_available_with_invalid_cwd_should_raise_exception():
    path_outside_of_repo = hdl_reuse.ROOT
    while exists(join(path_outside_of_repo, "..")):
        path_outside_of_repo = join(path_outside_of_repo, "..")

    with pytest.raises(RuntimeError) as exception_info:
        check_that_git_commands_are_available(cwd=path_outside_of_repo)
    assert str(exception_info.value).startswith("Could not run git")


def test_get_git_commit_without_local_changes():
    if git_local_changes_are_present():
        assert False, "Must be run from clean repo (on CI server or locally)"
    assert len(get_git_commit()) == 16


class TestGitCommitWithLocalChanges(unittest.TestCase):

    _trash_file = "local_file_for_git_test.apa"
    _trash_file_path = join(THIS_DIR, _trash_file)

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
