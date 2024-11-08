# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# A set of tools for versions and releases. Should be reusable between projects.
# --------------------------------------------------------------------------------------------------

# Standard libraries
import json
import re
import sys
from pathlib import Path
from urllib.request import urlopen

# Third party libraries
from git.repo import Repo
from packaging.version import Version, parse

# First party libraries
from tsfpga.system_utils import create_file, read_file

# Contents of unreleased.rst when it is empty
UNRELEASED_EMPTY = "Nothing here yet.\n"


class VersionNumberHandler:
    """
    Class for handling the version number in __init__.py.
    """

    _version_regexp = re.compile(r"\n__version__ = \"(\S+?)\"\n")

    def __init__(self, repo: Repo, version_file_path: Path) -> None:
        """
        Arguments:
            repo: The git repository to work with.
            version_file_path: The ``__init__.py`` file that shall be modified.
        """
        self._repo = repo
        self._file_path = version_file_path

    def update(self, new_version: str) -> None:
        """
        Set a new version number.

        Arguments:
            new_version: New version number as a string, e.g. "2.3.1".
        """
        old_version = self._get_current_version()
        self._verify_that_newer_version_number_is_greater_than_older(
            older_version=old_version, newer_version=new_version
        )

        self._set_new_version(new_version)

    def bump_to_prelease(self) -> None:
        """
        Bump to next version number. E.g. go from 8.0.2 to 8.0.3-dev.
        """
        current_version = self._get_current_version()
        (current_major, current_minor, current_patch) = current_version.release

        new_version = f"{current_major}.{current_minor}.{current_patch + 1}-dev"
        self._verify_that_newer_version_number_is_greater_than_older(
            older_version=current_version, newer_version=new_version
        )

        self._set_new_version(new_version)

    @staticmethod
    def _verify_that_newer_version_number_is_greater_than_older(
        older_version: Version, newer_version: str
    ) -> None:
        if older_version >= parse(newer_version):
            sys.exit(f"New version {newer_version} is not greater than old version {older_version}")

    def _get_current_version(self) -> Version:
        data = read_file(self._file_path)

        match = self._version_regexp.search(data)
        if match is None:
            raise RuntimeError(f"Could not find version value in {self._file_path}")

        version = match.group(1)
        return parse(version)

    def _set_new_version(self, new_version: str) -> None:
        data = read_file(self._file_path)

        updated_data = self._version_regexp.sub(f'\n__version__ = "{new_version}"\n', data)
        create_file(self._file_path, updated_data)

        # Add file so that it gets included in upcoming commit
        self._repo.index.add(str(self._file_path.resolve()))


def verify_new_version_number(
    repo: Repo, pypi_project_name: str, new_version: str, unreleased_notes_file: Path
) -> str:
    """
    Verify that the new version number is sane for this project. Will check git log and PyPI
    release history.

    Arguments:
        repo: The git repository to work with.
        pypi_project_name: The name of this project on PyPI.
        version: New version.
        unreleased_notes_file: Path to the "unreleased.rst" release notes file.
            Must not be empty.

    Return:
        The name of the git tag that corresponds to the new version number.
    """
    if repo.is_dirty():
        sys.exit("Must make release from clean repo")

    if read_file(unreleased_notes_file) in ["", UNRELEASED_EMPTY]:
        sys.exit(f"The unreleased notes file {unreleased_notes_file} should not be empty")

    with urlopen(f"https://pypi.python.org/pypi/{pypi_project_name}/json") as file_handle:
        json_data = json.load(file_handle)
        if new_version in json_data["releases"]:
            sys.exit(f"Release {new_version} already exists in PyPI")

    git_tag = f"v{new_version}"
    if git_tag in repo.tags:
        sys.exit(f"Git release tag already exists: {git_tag}")

    return git_tag


def commit_and_tag_release(repo: Repo, version: str, git_tag: str) -> None:
    """
    Make a git commit with a "release" message, and tag it.

    Arguments:
        repo: The git repository to work with.
        version: New version.
        git_tag: New git tag.
    """
    make_commit(repo=repo, commit_message=f"Release version {version}")

    repo.create_tag(git_tag)
    if git_tag not in repo.tags:
        sys.exit("Git tag failed")


def make_commit(repo: Repo, commit_message: str) -> None:
    """
    Make a git commit, and check that it worked.

    Arguments:
        repo: The git repository to work with.
        commit_message: Commit message to use.
    """
    repo.index.commit(commit_message)
    if repo.is_dirty():
        sys.exit("Git commit failed")
