# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from pathlib import Path
from shutil import which
import subprocess
import sys

PATH_TO_TSFPGA = Path(__file__).parent.parent.resolve()
sys.path.append(str(PATH_TO_TSFPGA))
PATH_TO_VUNIT = PATH_TO_TSFPGA.parent / "vunit"
sys.path.append(str(PATH_TO_VUNIT))

from vunit import VUnitCLI, VUnit
from vunit.vivado.vivado import create_compile_order_file, add_from_compile_order_file

import tsfpga
import tsfpga.create_vhdl_ls_config
from tsfpga.vivado_ip_cores import VivadoIpCores
from tsfpga.vivado_simlib import VivadoSimlib
from tsfpga.system_utils import create_directory

from examples.tsfpga_example_env import get_tsfpga_modules, TSFPGA_EXAMPLES_TEMP_DIR


def main():
    args = arguments()

    vunit_proj = VUnit.from_args(args=args)
    vunit_proj.add_verification_components()
    vunit_proj.add_random()
    vunit_proj.enable_location_preprocessing()
    vunit_proj.enable_check_preprocessing()

    all_modules = get_tsfpga_modules()
    has_commercial_simulator = vunit_proj.get_simulator_name() != "ghdl"

    if has_commercial_simulator and not args.vivado_skip:
        # Includes modules with IP cores. Can only be used with a commercial simulator.
        sim_modules = all_modules
    else:
        # Only modules that do not contain IP cores
        sim_modules = [module for module in all_modules if len(module.get_ip_core_files()) == 0]

    if args.vivado_skip:
        ip_core_vivado_project_sources_directory = None
    else:
        add_simlib(vunit_proj, args.temp_dir, args.simlib_compile)

        # Generate IP core simulation files. Will be used for the vhdl_ls config,
        # even if they are not added to the simulation project.
        ip_core_compile_order_file, ip_core_vivado_project_sources_directory \
            = generate_ip_core_files(all_modules, args.temp_dir, args.ip_compile)
        if has_commercial_simulator:
            add_from_compile_order_file(vunit_proj, ip_core_compile_order_file)

    create_vhdl_ls_configuration(PATH_TO_TSFPGA,
                                 vunit_proj,
                                 all_modules,
                                 ip_core_vivado_project_sources_directory)

    for module in sim_modules:
        vunit_library = vunit_proj.add_library(module.library_name)
        for hdl_file in module.get_simulation_files():
            if hdl_file.is_vhdl or hdl_file.is_verilog_source:
                vunit_library.add_source_file(hdl_file.path)
            else:
                assert False, f"Can not handle this file: {hdl_file}"
        module.setup_simulations(vunit_proj)

    vunit_proj.set_compile_option("ghdl.a_flags", ["-fpsl"])
    if vunit_proj.simulator_supports_coverage():
        vunit_proj.set_compile_option("enable_coverage", True)
        vunit_proj.set_sim_option("enable_coverage", True)
        vunit_proj.main(post_run=merge_ghdl_coverage)
    else:
        vunit_proj.main()


def arguments():
    cli = VUnitCLI()
    cli.parser.add_argument("--temp-dir",
                            type=Path,
                            default=TSFPGA_EXAMPLES_TEMP_DIR,
                            help="where to place files needed for simulation flow")
    cli.parser.add_argument("--vivado-skip",
                            action="store_true",
                            help="skip all steps that require Vivado")
    cli.parser.add_argument("--ip-compile",
                            action="store_true",
                            help="force (re)compile of IP cores")
    cli.parser.add_argument("--simlib-compile",
                            action="store_true",
                            help="force (re)compile of Vivado simlib")

    args = cli.parse_args()
    args.output_path = args.temp_dir / "vunit_out"
    return args


def add_simlib(vunit_proj, temp_dir, force_compile):
    vivado_simlib = VivadoSimlib.init(temp_dir, vunit_proj)
    if force_compile or vivado_simlib.compile_is_needed:
        vivado_simlib.compile()
        vivado_simlib.to_archive()
    vivado_simlib.add_to_vunit_project()


def generate_ip_core_files(modules, temp_dir, force_generate):
    vivado_ip_cores = VivadoIpCores(modules, temp_dir, "xc7z020clg400-1")

    if force_generate:
        vivado_ip_cores.create_vivado_project()
        vivado_project_created = True
    else:
        vivado_project_created = vivado_ip_cores.create_vivado_project_if_needed()

    if vivado_project_created:
        # If the IP core Vivado project has been (re)created we need to create
        # a new compile order file
        create_compile_order_file(vivado_ip_cores.vivado_project_file,
                                  vivado_ip_cores.compile_order_file)

    return vivado_ip_cores.compile_order_file, vivado_ip_cores.vivado_project_sources_directory


def create_vhdl_ls_configuration(output_path, vunit_proj, modules, ip_core_vivado_project_sources_directory):
    """
    Create config for vhdl_ls. Granted this might no be the "correct" place for this functionality.
    But since the call is somewhat quick (~10 ms), and simulate.py is run "often" it seems an
    appropriate place in order to always have an up-to-date vhdl_ls config.
    """
    vivado_location = None if which("vivado") is None else Path(which("vivado"))
    tsfpga.create_vhdl_ls_config.create_configuration(
        output_path=output_path,
        modules=modules,
        vunit_proj=vunit_proj,
        vivado_location=vivado_location,
        ip_core_vivado_project_sources_directory=ip_core_vivado_project_sources_directory)


def merge_ghdl_coverage(results):
    if not results.get_report().tests:
        print("No test results to merge coverage on")
        return

    temp_dir = results.get_report().output_path.parent

    merged_coverage_output = temp_dir / "vunit_coverage_database"
    results.merge_coverage(merged_coverage_output)

    report_html_path = temp_dir / "vhdl_coverage_html"
    create_directory(report_html_path, empty=True)
    gcovr_cmd = ["gcovr",
                 "--xml",
                 temp_dir / "vhdl_coverage.xml",
                 "--xml-pretty",
                 "--html",
                 "--html-details",
                 report_html_path / "index.html",
                 "--html-title",
                 "tsfpga VHDL coverage",
                 "--exclude-unreachable-branches",
                 "--exclude-throw-branches",
                 merged_coverage_output,
                 ]
    subprocess.call(gcovr_cmd)

    print(f"Coverage HTML report saved in {report_html_path}")


if __name__ == "__main__":
    main()
