# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import argparse
from pathlib import Path
import shutil
import sys

from git import Repo
from packaging.version import parse

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tsfpga import TSFPGA_PATH
from tsfpga.system_utils import create_file, delete, path_relative_to, read_file, run_command


def main():
    args = arguments()
    if not args.clean_and_build:
        sys.exit(
            "Must run with the --clean-and-build argument to verify that 'git clean' can be run"
        )

    # Remove stray files in the folder that is included in the release
    command = ["git", "clean", "-fdx", str(TSFPGA_PATH)]
    run_command(cmd=command, cwd=REPO_ROOT)

    # Checkout latest hdl_modules release tag, and find its SHA
    repo_location = delete(TSFPGA_PATH / "hdl_modules")
    tag, sha = checkout_latest_hdl_modules_release(destination=repo_location)

    # Move the "modules" folder to where we want to include it in the release
    modules_location = TSFPGA_PATH / f"hdl_modules_{tag}_{sha[0:10]}"
    shutil.move(repo_location / "modules", modules_location)

    # Delete the repo (shall not be included in release)
    delete(repo_location)

    # Update the definitions in __init__.py to point to the hdl_modules location
    init_py = TSFPGA_PATH / "__init__.py"
    init_py_before = read_file(init_py)
    modules_relative_location = path_relative_to(modules_location, TSFPGA_PATH)
    update_hdl_modules_information(
        file_path=init_py, relative_location=modules_relative_location, tag=tag, sha=sha
    )

    # Gather the release
    command = [sys.executable, "setup.py", "sdist"]
    run_command(cmd=command, cwd=REPO_ROOT)

    # Once the release has been gathered we can remove the "hdl_modules" folder and revert the
    # __init__.py definitions to "None"
    delete(modules_location)
    create_file(init_py, init_py_before)


def arguments():
    parser = argparse.ArgumentParser(
        "Build PyPI release. Will run a git clean before building.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--clean-and-build",
        action="store_true",
        help="this argument must be set for the script to run",
    )

    return parser.parse_args()


def checkout_latest_hdl_modules_release(destination):
    repo = Repo.clone_from(url="https://gitlab.com/tsfpga/hdl_modules.git", to_path=destination)

    tag = _get_greatest_version_tag(repo)
    print(f"Using the greatest version tag: {tag}")

    # "Checkout" per the instructions at
    # https://gitpython.readthedocs.io/en/stable/tutorial.html#switching-branches
    repo.head.reference = tag  # pylint: disable=assigning-non-slot
    assert not repo.head.is_detached
    repo.head.reset(index=True, working_tree=True)

    sha = repo.head.commit.hexsha

    return tag, sha


def _get_greatest_version_tag(repo):
    greatest_version = parse("0.0.0")
    greatest_tag = None

    for tag in repo.tags:
        # E.g. "v1.0.0" -> "1.0.0"
        tag_version_str = str(tag).split("v")[1]
        tag_version = parse(tag_version_str)

        if tag_version > greatest_version:
            greatest_version = tag_version
            greatest_tag = tag

    return greatest_tag


def update_hdl_modules_information(file_path, relative_location, tag, sha):
    data = read_file(file_path)

    data = data.replace(
        "\nHDL_MODULES_LOCATION = None\n",
        f'\nHDL_MODULES_LOCATION = TSFPGA_PATH / "{relative_location}"\n',
    )
    data = data.replace("\nHDL_MODULES_TAG = None\n", f'\nHDL_MODULES_TAG = "{tag}"\n')
    data = data.replace("\nHDL_MODULES_SHA = None\n", f'\nHDL_MODULES_SHA = "{sha}"\n')

    create_file(file_path, data)


if __name__ == "__main__":
    main()
