# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import sys
from pathlib import Path

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install.
REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

# Import before others since it modifies PYTHONPATH.
import tsfpga.examples.example_pythonpath  # noqa: F401

from tsfpga.build_project_list import BuildProjectList, get_build_projects
from tsfpga.examples.build_fpga_utils import arguments, collect_artifacts, setup_and_run
from tsfpga.examples.example_env import TSFPGA_EXAMPLES_TEMP_DIR, get_tsfpga_example_modules


def main() -> None:
    """
    Main function for building FPGA projects. If you are setting up a new build flow from scratch,
    you probably want to copy and modify this function, and reuse the others.
    """
    args = arguments(default_temp_dir=TSFPGA_EXAMPLES_TEMP_DIR)
    modules = get_tsfpga_example_modules()
    project_list = BuildProjectList(
        projects=get_build_projects(
            modules=modules,
            project_filters=args.project_filters,
            include_netlist_not_full_builds=args.netlist_builds,
        ),
        no_color=args.no_color,
    )

    sys.exit(
        setup_and_run(
            modules=modules,
            project_list=project_list,
            args=args,
            collect_artifacts_function=collect_artifacts,
        )
    )


if __name__ == "__main__":
    main()
