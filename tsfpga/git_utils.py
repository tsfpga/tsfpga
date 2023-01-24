# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import os
from pathlib import Path

# First party libraries
from tsfpga.system_utils import file_is_in_directory


def get_git_commit(directory):
    """
    Get a string describing the current git commit.
    E.g. ``"abcdef0123"`` or ``"12345678 (local changes present)"``.

    Arguments:
        directory (pathlib.Path): The directory where git commands will be run.

    Returns:
        str: Git commit information.
    """
    git_commit = get_git_sha(directory=directory)
    if git_local_changes_present(directory=directory):
        git_commit += " (local changes present)"

    return git_commit


def get_git_sha(directory):
    """
    Get a short git SHA.

    Arguments:
        directory (pathlib.Path): The directory where git commands will be run.

    Returns:
        str: The SHA.
    """
    # Generally, eight to ten characters are more than enough to be unique within a project.
    # The linux kernel, one of the largest projects, needs 11.
    # https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection#Short-SHA-1
    sha_length = 16

    if "GIT_COMMIT" in os.environ:
        return os.environ["GIT_COMMIT"][0:sha_length]

    # Import fails if "git" executable is not available, hence it can not be on top level.
    # This function should only be called if git is available.
    # pylint: disable=import-outside-toplevel
    # Third party libraries
    from git import Repo

    repo = Repo(directory, search_parent_directories=True)
    git_sha = repo.head.commit.hexsha[0:sha_length]

    return git_sha


def git_local_changes_present(directory):
    """
    Check if the git repo has local changes.

    Arguments:
        directory (pathlib.Path): The directory where git commands will be run.

    Returns:
        bool: ``True`` if the repo contains changes that have been made after the last commit.
    """
    # Import fails if "git" executable is not available, hence it can not be on top level.
    # This function should only be called if git is available.
    # pylint: disable=import-outside-toplevel
    # Third party libraries
    from git import Repo

    repo = Repo(directory, search_parent_directories=True)

    return repo.is_dirty()


def git_commands_are_available(directory):
    """
    True if "git" command executable is available, and ``directory`` is in a valid git repo.
    """
    try:
        # pylint: disable=import-outside-toplevel
        # Third party libraries
        from git import InvalidGitRepositoryError, Repo
    except ImportError:
        return False

    try:
        Repo(directory, search_parent_directories=True)
    except InvalidGitRepositoryError:
        return False

    return True


def find_git_files(
    directory,
    exclude_directories=None,
    file_endings_include=None,
    file_endings_avoid=None,
):
    """
    Find files that are checked in to git.

    Arguments:
        directory (pathlib.Path): Search in this directory.
        exclude_directories (list(pathlib.Path)): Files in these directories will not be included.
        file_endings_include (str or tuple(str)). Only files with these endings will be included.
        file_endings_avoid (str or tuple(str)): String or tuple of strings. Files with these endings
            will not be included.

    Returns:
        list(pathlib.Path): The files that are available in git.
    """

    # Import fails if "git" executable is not available, hence it can not be on top level.
    # This function should only be called if git is available.
    # pylint: disable=import-outside-toplevel
    # Third party libraries
    from git import Repo

    exclude_directories = (
        []
        if exclude_directories is None
        else [exclude_directory.resolve() for exclude_directory in exclude_directories]
    )

    def list_paths(root_tree, path):
        for blob in root_tree.blobs:
            yield path / blob.name
        for tree in root_tree.trees:
            yield from list_paths(tree, path / tree.name)

    repo = Repo(directory, search_parent_directories=True)
    repo_root = Path(repo.working_dir).resolve()

    for file_path in list_paths(repo.tree(), repo_root):
        if file_endings_include is not None and not file_path.name.endswith(file_endings_include):
            continue

        if file_endings_avoid is not None and file_path.name.endswith(file_endings_avoid):
            continue

        if file_is_in_directory(file_path, exclude_directories):
            continue

        if file_is_in_directory(file_path, [directory]):
            yield file_path
