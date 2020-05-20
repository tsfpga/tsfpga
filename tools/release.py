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

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

import tsfpga
from tsfpga.git_utils import find_git_files, git_local_changes_are_present, list_current_tags, list_tags
from tsfpga.system_utils import create_file, read_file, run_command


def main():
    parser = argparse.ArgumentParser(description="Make a release commit and tag")
    parser.add_argument("version",
                        nargs=1,
                        type=str,
                        help="version number MAJOR.MINOR.PATCH")
    version = parser.parse_args().version[0]

    git_tag = verify_version_number(version)

    init_py = tsfpga.TSFPGA_PATH / "__init__.py"
    update_version_number(version, init_py)

    commit_and_tag(version, git_tag, init_py)


def verify_version_number(version):
    if git_local_changes_are_present():
        sys.exit("Must make release from clean repo")

    release_notes_file = tsfpga.TSFPGA_DOC / "release_notes" / f"{version}.rst"
    if release_notes_file not in find_git_files():
        sys.exit(f"Could not find release notes file: {release_notes_file} (is it 'git add'ed?)")

    with urlopen("https://pypi.python.org/pypi/tsfpga/json") as file_handle:
        json_data = json.load(file_handle)
        if version in json_data["releases"]:
            sys.exit(f"Release {version} already exists in PyPI")

    git_tag = "v" + version
    if git_tag in list_tags():
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

    updated_file = version_regexp.sub(f"\n__version__ = \"{version}\"\n", data)
    create_file(file, updated_file)


def commit_and_tag(version, git_tag, file):
    command = ["git", "add", str(file.resolve())]
    run_command(command, cwd=REPO_ROOT)

    command = ["git", "commit", "-m", f"Release version {version}"]
    run_command(command, cwd=REPO_ROOT)
    if git_local_changes_are_present():
        sys.exit("Git commit failed")

    command = ["git", "tag", git_tag]
    run_command(command, cwd=REPO_ROOT)
    if git_tag not in list_current_tags():
        sys.exit("Git tag failed")


if __name__ == "__main__":
    main()
