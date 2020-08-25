# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------
# @eine has made a docker image that runs smoothly, run for example with:
#   docker run --rm --interactive --tty --volume ~/work/repo:/repo --workdir /repo/tsfpga ghdl/synth:formal /bin/bash
#   python3 examples/formal.py
# ------------------------------------------------------------------------------

import argparse
from pathlib import Path
import sys

PATH_TO_TSFPGA = Path(__file__).parent.parent.resolve()
sys.path.append(str(PATH_TO_TSFPGA))
PATH_TO_VUNIT = PATH_TO_TSFPGA.parent / "vunit"
sys.path.append(str(PATH_TO_VUNIT))

from tsfpga_example_env import get_tsfpga_modules, TSFPGA_EXAMPLES_TEMP_DIR
import tsfpga
from tsfpga.formal_project import FormalProject


def arguments(default_temp_dir=TSFPGA_EXAMPLES_TEMP_DIR):
    parser = argparse.ArgumentParser("Run formal tests",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--list-only",
                        action="store_true",
                        help="list the available tests")
    parser.add_argument("--project-path",
                        type=Path,
                        default=default_temp_dir / "formal_project",
                        help="the formal project will be placed here")
    args = parser.parse_args()

    return args


def main():
    args = arguments()
    modules = get_tsfpga_modules([tsfpga.TSFPGA_MODULES])
    formal_project = FormalProject(
        modules=modules,
        project_path=TSFPGA_EXAMPLES_TEMP_DIR / args.project_path)
    for module in modules:
        module.setup_formal(formal_project)

    if args.list_only:
        formal_project.list_tests()
        return

    formal_project.run()


if __name__ == "__main__":
    main()
