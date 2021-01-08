# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import os
from os.path import commonpath
from pathlib import Path


def get_git_commit(directory):
    """
    Generally, eight to ten characters are more than enough to be unique within a project.
    The linux kernel, one of the largest projects, needs 11.
    https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection#Short-SHA-1
    """
    sha_length = 16
    if "GIT_COMMIT" in os.environ:
        return os.environ["GIT_COMMIT"][0:sha_length]

    # Import fails if "git" executable is not available, hence it can not be on top level.
    # This function should only be called if git is available.
    # pylint: disable=import-outside-toplevel
    from git import Repo

    repo = Repo(directory)
    git_commit = repo.head.commit.hexsha[0:sha_length]
    if repo.is_dirty():
        git_commit += " (local changes present)"

    return git_commit


def git_commands_are_available(directory):
    """
    True if "git" command executable is available, and ``directory`` is in a valid git repo.
    """
    try:
        # pylint: disable=import-outside-toplevel
        from git import Repo, InvalidGitRepositoryError
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
    Arguments:
        file_endings_include (str or tuple(str)). Only files with these endings will be included.
        file_endings_avoid (str or tuple(str)): String or tuple of strings. Files with these endings
            will not be included.
        directory (`pathlib.Path`): Search in this directory.
        exclude_directories (list(`pathlib.Path`)): Files in these directories will not be included.
    """

    # Import fails if "git" executable is not available, hence it can not be on top level.
    # This function should only be called if git is available.
    # pylint: disable=import-outside-toplevel
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
    repo_root = Path(repo.git_dir).parent.resolve()

    for path in list_paths(repo.tree(), repo_root):
        if (file_endings_include is None or path.name.endswith(file_endings_include)) and (
            file_endings_avoid is None or not path.name.endswith(file_endings_avoid)
        ):
            if _file_is_in_directory(path, [directory]) and not _file_is_in_directory(
                path, exclude_directories
            ):
                yield path


def _file_is_in_directory(filename, directories):
    for directory in directories:
        if commonpath([str(filename), str(directory)]) == str(directory):
            return True
    return False
