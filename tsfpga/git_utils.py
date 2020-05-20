# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import os
from os.path import commonpath
from pathlib import Path
import subprocess

from tsfpga import REPO_ROOT


def get_git_commit(cwd=None):
    """
    Generally, eight to ten characters are more than enough to be unique within a project.
    The linux kernel, one of the largest projects, needs 11.
    https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection#Short-SHA-1
    """
    sha_length = 16
    if "GIT_COMMIT" in os.environ:
        return os.environ["GIT_COMMIT"][0:sha_length]

    check_that_git_commands_are_available(cwd)

    git_commit = get_git_sha(cwd)[0:sha_length]
    if git_local_changes_are_present(cwd):
        git_commit += " (local changes present)"

    return git_commit


def get_git_sha(cwd=None):
    command = ["git", "rev-parse", "HEAD"]
    output = subprocess.check_output(command, cwd=cwd, universal_newlines=True)
    return output


def git_local_changes_are_present(cwd=None):
    command = ["git", "diff-index", "--quiet", "HEAD", "--"]
    try:
        subprocess.check_call(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return True
    return False


def git_commands_are_available(cwd=None):
    command = ["git", "rev-parse", "--is-inside-work-tree"]
    try:
        subprocess.check_call(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return False
    return True


def check_that_git_commands_are_available(cwd=None):
    if not git_commands_are_available(cwd):
        mesg = "Could not run git. Is the command available on PATH? Is the script called from a repo?"
        raise RuntimeError(mesg)


def find_git_files(file_endings_include=None,
                   file_endings_avoid=None,
                   directory=REPO_ROOT,
                   exclude_directories=None):
    """
    Args:
        file_endings_include (str or tuple(str)). Only files with these endings will be included.
        file_endings_avoid (str or tuple(str)): String or tuple of strings. Files with these endings will not be included.
        directory (`pathlib.Path`): Search in this directory.
        exclude_directories (list(`pathlib.Path`)): Files in these directories will not be included.
    """
    exclude_directories = [] if exclude_directories is None else \
        [exclude_directory.resolve() for exclude_directory in exclude_directories]

    command = ["git", "ls-files"]
    output = subprocess.check_output(command, cwd=directory, universal_newlines=True)
    ls_files = output.split("\n")

    # subprocess.check_output() returns a trailing "\n". The split() call will make that an empty object at the end of the list.
    ls_files = ls_files[:-1]

    for file in ls_files:
        # git ls-files returns paths relative to the working directory where it's called. Hence we prepend the cwd used.
        # Normpath is necessary in windows where you can get a mix of slashes and backslashes which makes
        # path comparisons sketchy
        file = directory.joinpath(Path(file))
        assert file.exists()  # Make sure concatenation of relative path worked

        if file.is_file():  # "git ls-files" also lists submodule folders
            if (file_endings_include is None or file.name.endswith(file_endings_include)) \
                    and (file_endings_avoid is None or not file.name.endswith(file_endings_avoid)):
                if not _file_is_in_directory(file, exclude_directories):
                    yield file


def list_current_tags(cwd=REPO_ROOT):
    command = ["git", "tag", "--list", "--points-at", "HEAD"]
    return subprocess.check_output(command, cwd=cwd).decode().splitlines()


def list_tags(cwd=REPO_ROOT):
    command = ["git", "tag", "--list"]
    return subprocess.check_output(command, cwd=cwd).decode().splitlines()


def _file_is_in_directory(filename, directories):
    for directory in directories:
        if commonpath([str(filename), str(directory)]) == str(directory):
            return True
    return False
