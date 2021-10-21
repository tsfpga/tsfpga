# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import sys
from pathlib import Path

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
PATH_TO_TSFPGA = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PATH_TO_TSFPGA))

from tsfpga.examples.example_env import get_tsfpga_example_modules, TSFPGA_EXAMPLES_TEMP_DIR

import tsfpga
import tsfpga.create_vhdl_ls_config
from tsfpga.git_simulation_subset import GitSimulationSubset
from tsfpga.module import get_hdl_modules
from tsfpga.examples.simulation_utils import (
    create_vhdl_ls_configuration,
    get_arguments_cli,
    SimulationProject,
)


def main():
    """
    Main function for the simulation flow. If you are setting up a new simulation environment
    you probably want to copy and modify this function. The other functions and classes
    should be reusable in most cases.
    """
    cli = get_arguments_cli(default_output_path=TSFPGA_EXAMPLES_TEMP_DIR)
    args = cli.parse_args()

    modules = get_tsfpga_example_modules()
    modules_no_sim = get_hdl_modules()

    if args.vcs_minimal:
        if args.test_patterns != "*":
            sys.exit(
                "Can not specify a test pattern when using the --vcs-minimal flag."
                f" Got {args.test_patterns}",
            )

        test_filters = find_git_test_filters(
            args=args, repo_root=tsfpga.REPO_ROOT, modules=modules, modules_no_sim=modules_no_sim
        )
        if not test_filters:
            print("Nothing to run. Appears to be no VHDL-related git diff.")
            return

        # Override the test pattern argument to VUnit
        args.test_patterns = test_filters
        print(f"Running VUnit with test pattern {args.test_patterns}")

        # Enable minimal compilation in VUnit
        args.minimal = True

    simulation_project = SimulationProject(args=args)
    simulation_project.add_modules(args=args, modules=modules, modules_no_sim=modules_no_sim)
    ip_core_vivado_project_directory = simulation_project.add_vivado_simlib_and_ip_cores(
        args=args, modules=modules + modules_no_sim
    )

    create_vhdl_ls_configuration(
        output_path=tsfpga.REPO_ROOT,
        temp_files_path=TSFPGA_EXAMPLES_TEMP_DIR,
        modules=modules + modules_no_sim,
        ip_core_vivado_project_directory=ip_core_vivado_project_directory,
    )

    simulation_project.vunit_proj.main()


def find_git_test_filters(args, repo_root, modules, modules_no_sim=None, **setup_vunit_kwargs):
    """
    Construct a VUnit test filter that will run all test cases that are affected by git changes.
    The current git state is compared to origin/master, and differences are derived.
    See :class:`.GitSimulationSubset` for details.

    Arguments:
        args: Command line argument namespace.
        repo_root (pathlib.Path): Path to the repository root. Git commands will be run here.
        modules: Will be passed on to :meth:`.SimulationProject.add_modules`.
        modules_no_sim: Will be passed on to :meth:`.SimulationProject.add_modules`.
        setup_vunit_kwargs : Will be passed on to :meth:`.SimulationProject.add_modules`.

    Return:
        `list(str)`: A list of VUnit test case filters.
    """
    # Set up a dummy VUnit project that will be used for dependency scanning.
    # Note that sources are added identical to the "real" project above.
    simulation_project = SimulationProject(args=args)
    simulation_project.add_modules(
        args=args, modules=modules, modules_no_sim=modules_no_sim, **setup_vunit_kwargs
    )

    testbenches_to_run = GitSimulationSubset(
        repo_root=repo_root,
        reference_branch="origin/master",
        vunit_proj=simulation_project.vunit_proj,
        # We use VUnit preprocessing, so these arguments have to be supplied
        vunit_preprocessed_path=args.output_path / "preprocessed",
        modules=modules,
    ).find_subset()

    test_filters = []
    for testbench_file_name, library_name in testbenches_to_run:
        test_filters.append(f"{library_name}.{testbench_file_name}.*")

    return test_filters


if __name__ == "__main__":
    main()
