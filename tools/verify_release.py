# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import json
from pathlib import Path
import sys
from urllib.request import urlopen

REPO_ROOT = Path(__file__).parent.parent
sys.path.append(str(REPO_ROOT))

from tsfpga import TSFPGA_DOC
from tsfpga.git_utils import git_local_changes_are_present, list_current_tags
from tsfpga.about import get_version


def verify_release_version(version):
    if git_local_changes_are_present():
        sys.exit("Must make release from clean repo")

    release_notes_file = TSFPGA_DOC / "release_notes" / (version + ".rst")
    if not release_notes_file.exists():
        sys.exit(f"Could not find release notes file: {release_notes_file}")

    git_tag = "v" + version
    if git_tag not in list_current_tags():
        sys.exit("Could not find git tag: " + git_tag)

    with urlopen("https://pypi.python.org/pypi/tsfpga/json") as file_handle:
        json_data = json.load(file_handle)
        if version in json_data["releases"]:
            sys.exit(f"Release {version} already exists in PyPI")


if __name__ == "__main__":
    verify_release_version(get_version())
