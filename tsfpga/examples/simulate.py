# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import join, dirname, abspath
import sys

PATH_TO_TSFPGA = abspath(join(dirname(__file__), "..", ".."))
sys.path.append(PATH_TO_TSFPGA)
import tsfpga
from tsfpga.examples import MODULE_FOLDERS, MODULE_FOLDERS_WITH_IP
from tsfpga.module import get_modules
from tsfpga.registers import get_default_registers
from tsfpga.vivado_ip_cores import VivadoIpCores
from tsfpga.vivado_simlib import VivadoSimlib

PATH_TO_VUNIT = abspath(join(tsfpga.ROOT, "..", "..", "vunit"))
sys.path.append(PATH_TO_VUNIT)
from vunit import VUnitCLI, VUnit
from vunit.vivado.vivado import create_compile_order_file, add_from_compile_order_file


def main():
    args = arguments()

    if args.vivado_skip:
        modules = get_modules(MODULE_FOLDERS, default_registers=get_default_registers())
    else:
        modules = get_modules(MODULE_FOLDERS_WITH_IP, default_registers=get_default_registers())

    vunit_proj = VUnit.from_args(args=args)
    vunit_proj.add_verification_components()
    vunit_proj.add_random()
    vunit_proj.enable_location_preprocessing()
    vunit_proj.enable_check_preprocessing()

    if not args.vivado_skip:
        add_simlib(vunit_proj, args.temp_dir, args.simlib_compile)

        ip_core_compile_order_file = generate_ip_core_compile_order(modules, args.temp_dir, args.ip_compile)
        add_from_compile_order_file(vunit_proj, ip_core_compile_order_file)

    for module in modules:
        vunit_library = vunit_proj.add_library(module.library_name)
        for hdl_file in module.get_simulation_files():
            if hdl_file.is_vhdl or hdl_file.is_verilog_source:
                vunit_library.add_source_file(hdl_file.filename)
            else:
                assert False, "Can not handle this file: " + hdl_file.filename
        module.setup_simulations(vunit_proj)

    vunit_proj.main()


def arguments():
    cli = VUnitCLI()
    default_temp_directory = join(PATH_TO_TSFPGA, "generated")
    cli.parser.add_argument("--temp-dir",
                            type=str,
                            default=default_temp_directory,
                            help="where to place files needed for simulation flow")
    cli.parser.add_argument("--vivado-skip", action="store_true", help="skip all steps that require Vivado")
    cli.parser.add_argument("--ip-compile", action="store_true", help="force (re)compile of IP cores")
    cli.parser.add_argument("--simlib-compile", action="store_true", help="force (re)compile of Vivado simlib")

    args = cli.parse_args()
    args.output_path = join(args.temp_dir, "vunit_out")
    return args


def add_simlib(vunit_proj, temp_dir, force_compile):
    vivado_simlib = VivadoSimlib(vunit_proj, temp_dir)
    if force_compile:
        vivado_simlib.compile()
    else:
        vivado_simlib.compile_if_needed()
    vivado_simlib.add_to_vunit_project()


def generate_ip_core_compile_order(modules, temp_dir, force_generate):
    vivado_ip_cores = VivadoIpCores(modules, temp_dir)

    if force_generate:
        vivado_ip_cores.generate_files()
        ip_cores_generated = True
    else:
        ip_cores_generated = vivado_ip_cores.generate_files_if_needed()

    if ip_cores_generated:
        # If IP cores have been (re)generated we need to create a new compile order file
        create_compile_order_file(vivado_ip_cores.vivado_project_file, vivado_ip_cores.compile_order_file)

    return vivado_ip_cores.compile_order_file


if __name__ == "__main__":
    main()
