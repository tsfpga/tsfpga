# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import argparse
import json
from pathlib import Path
import re
from shutil import move
import sys
from urllib.request import urlopen

from packaging.version import parse
from git import Repo

PATH_TO_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PATH_TO_REPO_ROOT))

import tsfpga
from tsfpga.system_utils import create_file, read_file

UNRELEASED_EMPTY = "Nothing here yet.\n"


def main():
    parser = argparse.ArgumentParser(description="Make release commits and tag")
    parser.add_argument(
        "release_version", nargs=1, type=str, help="release version number MAJOR.MINOR.PATCH"
    )
    release_version = parser.parse_args().release_version[0]

    repo = Repo(tsfpga.REPO_ROOT)
    git_tag = verify_new_version_number(repo=repo, new_version=release_version)

    version_number_handler = VersionNumberHandler(repo=repo)
    version_number_handler.update(new_version=release_version)

    move_release_notes(repo=repo, version=release_version)

    commit_and_tag_release(repo=repo, version=release_version, git_tag=git_tag)

    version_number_handler.bump_to_prelease()
    make_commit(repo=repo, commit_message="Set pre-release version number")


def verify_new_version_number(repo, new_version):
    if repo.is_dirty():
        sys.exit("Must make release from clean repo")

    unreleased_notes_file = tsfpga.TSFPGA_DOC / "release_notes" / "unreleased.rst"
    if read_file(unreleased_notes_file) in ["", UNRELEASED_EMPTY]:
        sys.exit(f"The unreleased notes file {unreleased_notes_file} should not be empty")

    with urlopen("https://pypi.python.org/pypi/tsfpga/json") as file_handle:
        json_data = json.load(file_handle)
        if new_version in json_data["releases"]:
            sys.exit(f"Release {new_version} already exists in PyPI")

    git_tag = "v" + new_version
    if git_tag in repo.tags:
        sys.exit(f"Git release tag already exists: {git_tag}")

    return git_tag


class VersionNumberHandler:

    _file_path = tsfpga.TSFPGA_PATH / "__init__.py"
    _version_regexp = re.compile(r"\n__version__ = \"(\S+?)\"\n")

    def __init__(self, repo):
        self._repo = repo

    def update(self, new_version):
        """
        Set the new version number supplied (string).
        """
        old_version = self._get_current_version()
        self._verify_that_newer_version_number_is_greater_than_older(
            older_version=old_version, newer_version=new_version
        )

        self._set_new_version(new_version)

    def bump_to_prelease(self):
        """
        Bump to next version number. E.g. go from 8.0.2 to 8.0.3-dev.
        """
        current_version = self._get_current_version()
        (major, minor, patch) = current_version.release
        new_version = f"{major}.{minor}.{patch + 1}-dev"
        self._verify_that_newer_version_number_is_greater_than_older(
            older_version=current_version, newer_version=new_version
        )

        self._set_new_version(new_version)

    @staticmethod
    def _verify_that_newer_version_number_is_greater_than_older(older_version, newer_version):
        if older_version >= parse(newer_version):
            sys.exit(f"New version {newer_version} is not greater than old version {older_version}")

    def _get_current_version(self):
        data = read_file(self._file_path)

        match = self._version_regexp.search(data)
        if match is None:
            raise RuntimeError(f"Could not find version value in {self._file_path}")

        version = match.group(1)
        return parse(version)

    def _set_new_version(self, new_version):
        data = read_file(self._file_path)

        updated_data = self._version_regexp.sub(f'\n__version__ = "{new_version}"\n', data)
        create_file(self._file_path, updated_data)

        # Add file so that it gets included in upcoming commit
        self._repo.index.add(str(self._file_path.resolve()))


def move_release_notes(repo, version):
    unreleased_rst = tsfpga.TSFPGA_DOC / "release_notes" / "unreleased.rst"
    version_rst = tsfpga.TSFPGA_DOC / "release_notes" / f"{version}.rst"

    if version_rst.exists():
        raise RuntimeError(f"Release notes already exist: {version_rst}")

    move(unreleased_rst, version_rst)

    # Create a new, empty, unreleased notes file
    create_file(unreleased_rst, UNRELEASED_EMPTY)

    # Add files so that the changes get included in the commit
    repo.index.add(str(unreleased_rst.resolve()))
    repo.index.add(str(version_rst.resolve()))


def commit_and_tag_release(repo, version, git_tag):
    make_commit(repo=repo, commit_message=f"Release version {version}")

    repo.create_tag(git_tag)
    if git_tag not in repo.tags:
        sys.exit("Git tag failed")


def make_commit(repo, commit_message):
    repo.index.commit(commit_message)
    if repo.is_dirty():
        sys.exit("Git commit failed")


if __name__ == "__main__":
    main()
