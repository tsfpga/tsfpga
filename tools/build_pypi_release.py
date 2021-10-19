# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import argparse
from pathlib import Path
import sys

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tsfpga.system_utils import run_command


def main():
    args = arguments()
    if not args.clean_and_build:
        sys.exit(
            "Must run with the --clean-and-build argument to verify that 'git clean' can be run"
        )

    # Remove stray files in the two folders that are included in the release
    command = ["git", "clean", "-fdx", "tsfpga", "modules"]
    run_command(cmd=command, cwd=REPO_ROOT)

    command = [sys.executable, "setup.py", "sdist"]
    run_command(cmd=command, cwd=REPO_ROOT)


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


if __name__ == "__main__":
    main()
