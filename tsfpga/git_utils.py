# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from tsfpga.system_utils import file_is_in_directory

if TYPE_CHECKING:
    from collections.abc import Iterator

    from git.objects.tree import Tree


def get_git_commit(directory: Path, use_rst_annotation: bool = False) -> str:
    """
    Get a string describing the current git commit.
    E.g. ``"abcdef0123"`` or ``"12345678 (local changes present)"``.

    Arguments:
        directory: The directory where git commands will be run.
        use_rst_annotation: Use reStructuredText literal annotation for the SHA value.

    Return:
        Git commit information.
    """
    annotation = "``" if use_rst_annotation else ""
    git_sha = get_git_sha(directory=directory)
    result = f"{annotation}{git_sha}{annotation}"

    if git_local_changes_present(directory=directory):
        result += " (local changes present)"

    return result


def get_git_sha(directory: Path) -> str:
    """
    Get a short git SHA.

    Arguments:
        directory: The directory where git commands will be run.

    Return:
        The SHA.
    """
    # Generally, eight to ten characters are more than enough to be unique within a project.
    # The linux kernel, one of the largest projects, needs 12.
    # https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection#Short-SHA-1
    sha_length = 12

    if "GIT_COMMIT" in os.environ:
        return os.environ["GIT_COMMIT"][0:sha_length]

    # Import fails if "git" executable is not available, hence it can not be on top level.
    # This function should only be called if git is available.
    from git.repo import Repo  # noqa: PLC0415

    repo = Repo(directory, search_parent_directories=True)
    return repo.head.commit.hexsha[0:sha_length]


def git_local_changes_present(directory: Path) -> bool:
    """
    Check if the git repo has local changes.

    Arguments:
        directory: The directory where git commands will be run.

    Return:
        ``True`` if the repo contains changes that have been made after the last commit.
    """
    # Import fails if "git" executable is not available, hence it can not be on top level.
    # This function should only be called if git is available.
    from git.repo import Repo  # noqa: PLC0415

    repo = Repo(directory, search_parent_directories=True)

    return repo.is_dirty()


def git_commands_are_available(directory: Path) -> bool:
    """
    True if "git" command executable is available, and ``directory`` is in a valid git repo.
    """
    try:
        from git import InvalidGitRepositoryError  # noqa: PLC0415
        from git.repo import Repo  # noqa: PLC0415
    except ImportError:
        return False

    try:
        Repo(directory, search_parent_directories=True)
    except InvalidGitRepositoryError:
        return False

    return True


def find_git_files(
    directory: Path,
    exclude_directories: list[Path] | None = None,
    file_endings_include: str | tuple[str] | None = None,
    file_endings_avoid: str | tuple[str] | None = None,
) -> Iterator[Path]:
    """
    Find files that are checked in to git.

    Arguments:
        directory: Search in this directory.
        exclude_directories: Files in these directories will not be included.
        file_endings_include: Only files with these endings will be included.
        file_endings_avoid: Files with these endings will not be included.

    Return:
        The files that are available in git.
    """
    # Import fails if "git" executable is not available, hence it can not be on top level.
    # This function should only be called if git is available.
    from git.repo import Repo  # noqa: PLC0415

    exclude_directories = (
        []
        if exclude_directories is None
        else [exclude_directory.resolve() for exclude_directory in exclude_directories]
    )

    def list_paths(root_tree: Tree, path: Path) -> Iterator[Path]:
        for blob in root_tree.blobs:
            yield path / blob.name
        for tree in root_tree.trees:
            yield from list_paths(tree, path / tree.name)

    repo = Repo(directory, search_parent_directories=True)
    repo_root = Path(repo.working_dir).resolve()

    for file_path in list_paths(root_tree=repo.tree(), path=repo_root):
        if file_endings_include is not None and not file_path.name.endswith(file_endings_include):
            continue

        if file_endings_avoid is not None and file_path.name.endswith(file_endings_avoid):
            continue

        if file_is_in_directory(file_path, exclude_directories):
            continue

        if file_is_in_directory(file_path, [directory]):
            yield file_path
