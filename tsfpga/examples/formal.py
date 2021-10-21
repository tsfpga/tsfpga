# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# The tsfpga/formal docker image can be used to run this file. See run_formal.sh
# --------------------------------------------------------------------------------------------------

import argparse
from pathlib import Path
import sys

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
PATH_TO_TSFPGA = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PATH_TO_TSFPGA))

from tsfpga.examples.example_env import TSFPGA_EXAMPLES_TEMP_DIR

from tsfpga.formal_project import FormalProject
from tsfpga.module import get_hdl_modules
from tsfpga.system_utils import delete


def arguments(default_temp_dir=TSFPGA_EXAMPLES_TEMP_DIR):
    """
    Setup of arguments for the example build flow.

    Arguments:
        default_temp_dir (pathlib.Path): Default value for output paths.
    """
    parser = argparse.ArgumentParser(
        "Run formal tests", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--list-only", action="store_true", help="list the available tests")

    parser.add_argument("--clean-only", action="store_true", help="clears the project path")

    parser.add_argument(
        "--project-path",
        type=Path,
        default=default_temp_dir / "formal_project",
        help="the formal project will be placed here",
    )

    parser.add_argument("test_filters", nargs="*", default="*", help="Tests to run")

    parser.add_argument(
        "--num-threads",
        "-p",
        type=int,
        default=8,
        help="number of threads to use when building project",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print all build output, even if the run is successful",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="do not print any build output, even if the run has failed",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable color in printouts",
    )

    args = parser.parse_args()

    return args


def main():
    """
    Main function for running formal test. If you are setting up a new formal flow from scratch,
    you probably want to copy and modify this function.
    """
    args = arguments()

    if args.clean_only:
        delete(args.project_path)
        return

    modules = get_hdl_modules()
    formal_project = FormalProject(modules=modules, project_path=args.project_path)
    for module in modules:
        module.setup_formal(formal_project)

    if args.list_only:
        formal_project.list_tests(args.test_filters)
        return

    all_build_ok = formal_project.run(
        num_threads=args.num_threads,
        verbose=args.verbose,
        quiet=args.quiet,
        test_filters=args.test_filters,
        no_color=args.no_color,
    )

    if not all_build_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
