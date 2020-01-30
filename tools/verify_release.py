# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import json
from os.path import dirname, exists, join
import subprocess
import sys
from urllib.request import urlopen

ROOT = join(dirname(__file__), "..")
sys.path.append(ROOT)

from tsfpga.git_utils import git_local_changes_are_present
from tsfpga.about import get_version


def verify_release_version(version):
    if git_local_changes_are_present():
        sys.exit("Must make release from clean repo")

    release_notes_file = join(ROOT, "doc", "release_notes", version + ".md")
    if not exists(release_notes_file):
        sys.exit("Could not find release notes file: " + release_notes_file)

    git_tag = "v" + version
    git_tags = subprocess.check_output(
        ["git", "tag", "--list", "--points-at", "HEAD"]).decode().splitlines()
    if git_tag not in git_tags:
        sys.exit("Could not find correspoing git tag: " + git_tag)

    with urlopen("https://pypi.python.org/pypi/tsfpga/json") as file_handle:
        json_data = json.load(file_handle)
        if version in json_data["releases"]:
            sys.exit(f"Release {version} already exists in PyPI")


if __name__ == "__main__":
    verify_release_version(get_version())
