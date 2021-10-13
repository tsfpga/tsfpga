# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import argparse
from shutil import which
import sys
from pathlib import Path

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
PATH_TO_TSFPGA = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PATH_TO_TSFPGA))
PATH_TO_VUNIT = PATH_TO_TSFPGA.parent / "vunit"
sys.path.insert(0, str(PATH_TO_VUNIT))

from vunit import VUnitCLI, VUnit
from vunit.vivado.vivado import create_compile_order_file, add_from_compile_order_file

import tsfpga
import tsfpga.create_vhdl_ls_config
from tsfpga.module import ModuleList
from tsfpga.vivado.ip_cores import VivadoIpCores
from tsfpga.vivado.simlib import VivadoSimlib


def get_arguments_cli(default_output_path):
    """
    Get arguments for the simulation flow.

    Arguments:
        default_output_path (`pathlib.Path`): Will be set as default for output path arguments
            (both VUnit files and Vivado files).
    """
    cli = VUnitCLI()

    # Print default values when doing --help
    cli.parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

    # Set the supplied default value for VUnit output path. pylint: disable=protected-access
    for action in cli.parser._actions:
        if action.dest == "output_path":
            action.default = default_output_path / "vunit_out"
            break
    else:
        raise AssertionError("VUnit --output-path argument not found")

    cli.parser.add_argument(
        "--output-path-vivado",
        type=Path,
        default=default_output_path,
        help=(
            "where to place Vivado IP core and simlib files. "
            "Note that --output-path is for VUnit files"
        ),
    )

    cli.parser.add_argument(
        "--vivado-skip", action="store_true", help="skip all steps that require Vivado"
    )

    cli.parser.add_argument(
        "--ip-compile", action="store_true", help="force (re)compile of IP cores"
    )

    cli.parser.add_argument(
        "--simlib-compile", action="store_true", help="force (re)compile of Vivado simlib"
    )

    cli.parser.add_argument(
        "--vcs-minimal",
        action="store_true",
        help="compile and run only a minimal set of tests based on Version Control System history",
    )

    return cli


class SimulationProject:
    """
    Class for setting up and handling a VUnit simulation project. Should be reusable in most cases.
    """

    def __init__(self, args, preprocessing_disable=False):
        """
        Create a VUnit project, configured according to the given arguments.

        Arguments:
            preprocessing_disable (bool): If ``True``, VUnit location/check preprocessing will not
                be enabled.

        Return: The created VUnit project.
        """
        self.vunit_proj = VUnit.from_args(args=args)
        self.vunit_proj.add_verification_components()
        self.vunit_proj.add_random()
        if not preprocessing_disable:
            self.vunit_proj.enable_location_preprocessing()
            self.vunit_proj.enable_check_preprocessing()

        self.has_commercial_simulator = self.vunit_proj.get_simulator_name() != "ghdl"

    def add_modules(self, args, modules, modules_no_sim=None, **setup_vunit_kwargs):
        """
        Add module source files to the VUnit project.

        Arguments:
            args: Command line argument namespace.
            modules (:class:`.ModuleList`): These modules will be included in the
                simulation project.
            modules_no_sim (:class:`.ModuleList`): These modules will be included in the simulation
                project, but their test files will not be added.
            setup_vunit_kwargs: Further arguments that will be sent to
                :meth:`.BaseModule.setup_vunit` for each module. Note that this is a "kwargs" style
                argument; any number of named arguments can be sent.
        """
        modules_no_sim = ModuleList() if modules_no_sim is None else modules_no_sim
        all_modules = modules + modules_no_sim

        if self.has_commercial_simulator and not args.vivado_skip:
            # Includes modules with IP cores. Can only be used with a commercial simulator.
            available_modules = all_modules
        else:
            # Exclude modules that contain IP cores
            available_modules = [module for module in all_modules if not module.get_ip_core_files()]

        for module in available_modules:
            vunit_library = self.vunit_proj.add_library(module.library_name)
            simulate_this_module = module not in modules_no_sim

            for hdl_file in module.get_simulation_files(include_tests=simulate_this_module):
                if hdl_file.is_vhdl or hdl_file.is_verilog_source:
                    vunit_library.add_source_file(hdl_file.path)
                else:
                    assert False, f"Can not handle this file: {hdl_file}"

            if simulate_this_module:
                module.setup_vunit(vunit_proj=self.vunit_proj, **setup_vunit_kwargs)

    def add_vivado_simlib_and_ip_cores(
        self,
        args,
        modules,
        vivado_part_name="xc7z020clg400-1",
        vivado_ip_core_project_class=None,
    ):
        """
        Add Vivado simlib and module IP cores to the VUnit project.
        Will compile and add simlib unless instructed not to by ``args``.
        When running with a commercial simulator, IP cores will be generated and added,
        unless instructed not to by ``args``.

        Arguments:
            args: Command line argument namespace.
            modules (:class:`.ModuleList`): IP cores from these modules will be included in the
                simulation project.
            vivado_part_name (str): Part name to be used for Vivado IP core project. Might have to
                change from default depending on what parts you have available in your
                Vivado installation.
            vivado_ip_core_project_class: Class to be used for Vivado IP core project. Can be left
                at default in most cases.

        Return:
            `pathlib.Path`: Path to the Vivado IP core project's ``project`` directory.
        """
        if args.vivado_skip:
            return None

        self._add_simlib(output_path=args.output_path_vivado, force_compile=args.simlib_compile)

        # Generate IP core simulation files. Might be used for the vhdl_ls config,
        # even if they are not added to the simulation project.
        (
            ip_core_compile_order_file,
            ip_core_vivado_project_directory,
        ) = self._generate_ip_core_files(
            modules=modules,
            output_path=args.output_path_vivado,
            force_generate=args.ip_compile,
            part_name=vivado_part_name,
            vivado_project_class=vivado_ip_core_project_class,
        )
        if self.has_commercial_simulator:
            add_from_compile_order_file(
                vunit_obj=self.vunit_proj, compile_order_file=ip_core_compile_order_file
            )

        return ip_core_vivado_project_directory

    def _add_simlib(self, output_path, force_compile):
        """
        Add Vivado simlib to the VUnit project. Compile if needed.

        .. note::

            This method can be overloaded in a child class if you want to do something more
            advanced, e.g. fetching compiled simlib from Artifactory.

        Arguments:
            vunit_proj: Vivado simlib will be added to this VUnit project.
            output_path (`pathlib.Path`): Compiled simlib will be placed in sub-directory of
                this path.
            force_compile (bool): Will (re)-compile simlib even if compiled artifacts exist.
        """
        vivado_simlib = VivadoSimlib.init(output_path, self.vunit_proj)
        if force_compile or vivado_simlib.compile_is_needed:
            vivado_simlib.compile()
            vivado_simlib.to_archive()
        vivado_simlib.add_to_vunit_project()

    @staticmethod
    def _generate_ip_core_files(
        modules, output_path, force_generate, part_name, vivado_project_class=None
    ):
        """
        Generate Vivado IP core files that are to be added to the VUnit project.
        Create a new project to generate files if needed.

        Arguments:
            modules (:class:`.ModuleList`): IP cores from these modules will be included.
            output_path (`pathlib.Path`): IP core files will be placed in sub-directory of
                this path.
            force_generate (bool): Will (re)-generate files even if they exist.
            part_name (str): Vivado part name.
            vivado_project_class: Class to be used for Vivado IP core project.
        """
        vivado_ip_cores = VivadoIpCores(
            modules=modules,
            output_path=output_path,
            part_name=part_name,
            vivado_project_class=vivado_project_class,
        )

        if force_generate:
            vivado_ip_cores.create_vivado_project()
            vivado_project_created = True
        else:
            vivado_project_created = vivado_ip_cores.create_vivado_project_if_needed()

        if vivado_project_created:
            # If the IP core Vivado project has been (re)created we need to create
            # a new compile order file
            create_compile_order_file(
                vivado_ip_cores.vivado_project_file, vivado_ip_cores.compile_order_file
            )

        return vivado_ip_cores.compile_order_file, vivado_ip_cores.project_directory


def create_vhdl_ls_configuration(
    output_path, temp_files_path, modules, ip_core_vivado_project_directory
):
    """
    Create config for vhdl_ls (https://github.com/VHDL-LS/rust_hdl).
    Granted this might no be the "correct" place for this functionality.
    But since the call is somewhat quick (~10 ms), and simulate.py is run "often" it seems an
    appropriate place in order to always have an up-to-date vhdl_ls config.

    Arguments:
        output_path (`pathlib.Path`): Config file will be placed here.
        temp_files_path (`pathlib.Path`): Some temporary files will be placed here.
        modules (:class:`.ModuleList`): These modules will be added.
        ip_core_vivado_project_directory (`pathlib.Path`): Vivado IP core files in this location
            will be added.
    """
    # Create an empty VUnit project to add files from VUnit and OSVVM library.
    # If we were to use the "real" VUnit project that we set up above instead, all the files would
    # be in the "preprocessed" folder. Hence we use an "empty" VUnit project, and add all files
    # via modules.
    vunit_proj = VUnit.from_argv(argv=["--output-path", str(temp_files_path / "vhdl_ls_vunit_out")])
    vunit_proj.add_verification_components()
    vunit_proj.add_random()
    vunit_proj.add_osvvm()

    vivado_location = None if which("vivado") is None else Path(which("vivado"))
    tsfpga.create_vhdl_ls_config.create_configuration(
        output_path=output_path,
        modules=modules,
        vunit_proj=vunit_proj,
        vivado_location=vivado_location,
        ip_core_vivado_project_directory=ip_core_vivado_project_directory,
    )