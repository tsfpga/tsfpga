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
import tsfpga.examples.example_pythonpath

import tsfpga
from tsfpga.create_ghdl_ls_config import create_ghdl_ls_configuration
from tsfpga.examples.example_env import (
    TSFPGA_EXAMPLES_TEMP_DIR,
    get_hdl_modules,
    get_tsfpga_example_modules,
)
from tsfpga.examples.simulation_utils import (
    NoVcsDiffTestsFound,
    SimulationProject,
    create_vhdl_ls_configuration,
    find_git_test_filter,
    get_arguments_cli,
)


def main() -> None:
    """
    Main function for the simulation flow. If you are setting up a new simulation environment
    you probably want to copy and modify this function. The other functions and classes
    should be reusable in most cases.
    """
    cli = get_arguments_cli(default_output_path=TSFPGA_EXAMPLES_TEMP_DIR)
    args = cli.parse_args()

    modules = get_tsfpga_example_modules()
    modules_no_test = get_hdl_modules()

    if args.vcs_minimal:
        try:
            args = find_git_test_filter(
                args=args,
                repo_root=tsfpga.REPO_ROOT,
                modules=modules,
                modules_no_test=modules_no_test,
            )
        except NoVcsDiffTestsFound:
            print("Nothing to run. Appears to be no VHDL-related git diff.")
            return

    simulation_project = SimulationProject(args=args)
    ip_core_vivado_project_directory = simulation_project.add_vivado_ip_cores(
        modules=modules + modules_no_test
    )

    # Generate before modules are added to VUnit project, to avoid duplicate files.
    create_vhdl_ls_configuration(
        output_path=tsfpga.REPO_ROOT,
        modules=modules + modules_no_test,
        vunit_proj=simulation_project.vunit_proj,
        ip_core_vivado_project_directory=ip_core_vivado_project_directory,
    )

    simulation_project.add_modules(
        args=args,
        modules=modules,
        modules_no_test=modules_no_test,
        include_verilog_files=False,
        include_systemverilog_files=False,
    )

    # Synopsys is needed by unisim MMCME2_ADV primitive.
    # Relaxed rules needed by unisim VITAL2000 package.
    # Do not use in any new code.
    simlib = simulation_project.add_vivado_simlib()
    simulation_project.vunit_proj.set_sim_option("ghdl.elab_flags", ["-fsynopsys", "-frelaxed"])

    create_ghdl_ls_configuration(
        output_path=tsfpga.REPO_ROOT,
        modules=modules + modules_no_test,
        vunit_proj=simulation_project.vunit_proj,
        simlib=simlib,
    )

    simulation_project.vunit_proj.main()


if __name__ == "__main__":
    main()
