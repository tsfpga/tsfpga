from os.path import abspath
import pytest
import subprocess

from hdl_reuse.system_utils import find_git_files, run_command


THIS_FILE = abspath(__file__)


def test_this_file_is_listed_by_find_git_files_without_argument():
    git_files = find_git_files()
    assert THIS_FILE in git_files


def test_this_file_is_listed_by_find_git_files_with_argument():
    git_files = find_git_files(file_ending="py")
    assert THIS_FILE in git_files


def test_this_file_is_not_listed_by_find_git_files_with_bad_argument():
    git_files = find_git_files(file_ending="vhd")
    assert THIS_FILE not in git_files


def test_run_command_called_with_nonexisting_binary_should_raise_exception():
    cmd = ["/apa/hest/zebra.exe", "foobar"]
    with pytest.raises(FileNotFoundError):
        run_command(cmd)


def test_run_command_with_non_zero_return_code_should_raise_exception():
    cmd = ["ls", "/apa/hest/zebra"]
    with pytest.raises(subprocess.CalledProcessError):
        run_command(cmd)


def test_run_command_called_with_non_list_should_raise_exception():
    cmd = ["ls", "-la"]
    run_command(cmd)

    cmd = "ls -la"
    with pytest.raises(ValueError) as exception_info:
        run_command(cmd)
    assert str(exception_info.value).startswith("Must be called with a list")
