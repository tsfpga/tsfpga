# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.request import urlopen

from packaging.version import parse
from git import Repo

PATH_TO_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PATH_TO_REPO_ROOT))

import tsfpga
from tsfpga.git_utils import find_git_files
from tsfpga.system_utils import create_file, read_file


def main():
    parser = argparse.ArgumentParser(description="Make a release commit and tag")
    parser.add_argument("version", nargs=1, type=str, help="version number MAJOR.MINOR.PATCH")
    version = parser.parse_args().version[0]

    repo = Repo(tsfpga.REPO_ROOT)
    git_tag = verify_version_number(repo, version)

    init_py = tsfpga.TSFPGA_PATH / "__init__.py"
    update_version_number(version, init_py)

    commit_and_tag(repo, version, git_tag, init_py)


def verify_version_number(repo, version):
    if repo.is_dirty():
        sys.exit("Must make release from clean repo")

    release_notes_file = tsfpga.TSFPGA_DOC / "release_notes" / f"{version}.rst"
    if release_notes_file not in find_git_files(directory=tsfpga.REPO_ROOT):
        sys.exit(f"Could not find release notes file: {release_notes_file} (is it 'git add'ed?)")

    unreleased_notes_file = tsfpga.TSFPGA_DOC / "release_notes" / "unreleased.rst"
    if read_file(unreleased_notes_file) != "":
        sys.exit("The unreleased notes file should be empty")

    with urlopen("https://pypi.python.org/pypi/tsfpga/json") as file_handle:
        json_data = json.load(file_handle)
        if version in json_data["releases"]:
            sys.exit(f"Release {version} already exists in PyPI")

    git_tag = "v" + version
    if git_tag in repo.tags:
        sys.exit(f"Git release tag already exists: {git_tag}")

    return git_tag


def update_version_number(version, file):
    data = read_file(file)
    version_regexp = re.compile(r"\n__version__ = \"(\S+?)\"\n")

    match = version_regexp.search(data)
    if match is None:
        raise RuntimeError(f"Could not find version value in {file}")

    old_version = match.group(1)
    if parse(old_version) >= parse(version):
        sys.exit(f"New version is not greater than old version {old_version}")

    updated_file = version_regexp.sub(f'\n__version__ = "{version}"\n', data)
    create_file(file, updated_file)


def commit_and_tag(repo, version, git_tag, file):
    repo.index.add(str(file))
    repo.index.commit(f"Release version {version}")
    if repo.is_dirty():
        sys.exit("Git commit failed")

    repo.create_tag(git_tag)
    if git_tag not in repo.tags:
        sys.exit("Git tag failed")


if __name__ == "__main__":
    main()
