# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import argparse
from pathlib import Path
from shutil import which
from typing import TYPE_CHECKING, Any, Optional, Type

if TYPE_CHECKING:
    from tsfpga.vivado.simlib_common import VivadoSimlibCommon

# Third party libraries
from vunit.ui import VUnit
from vunit.vivado.vivado import add_from_compile_order_file, create_compile_order_file
from vunit.vunit_cli import VUnitCLI

# First party libraries
import tsfpga
import tsfpga.create_vhdl_ls_config
from tsfpga.module_list import ModuleList
from tsfpga.vivado.ip_cores import VivadoIpCores
from tsfpga.vivado.simlib import VivadoSimlib


def get_arguments_cli(default_output_path: Path) -> VUnitCLI:
    """
    Get arguments for the simulation flow.

    Arguments:
        default_output_path: Will be set as default for output path arguments
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

    cli.parser.add_argument(
        "--inspect",
        action="store_true",
        help="optionally inspect some simulation result. Is only available for some modules",
    )

    return cli


class SimulationProject:
    """
    Class for setting up and handling a VUnit simulation project. Should be reusable in most cases.
    """

    def __init__(self, args: argparse.Namespace, enable_preprocessing: bool = False) -> None:
        """
        Create a VUnit project, configured according to the given arguments.

        Arguments:
            args: Command line argument namespace from ``simulate.py``.
            enable_preprocessing: If ``True``, VUnit location/check preprocessing will be enabled.
        """
        self.args = args

        self.vunit_proj = VUnit.from_args(args=args)
        self.vunit_proj.add_vhdl_builtins()
        self.vunit_proj.add_verification_components()
        self.vunit_proj.add_random()

        if enable_preprocessing:
            self.vunit_proj.enable_location_preprocessing()
            self.vunit_proj.enable_check_preprocessing()

        self.has_commercial_simulator = self.vunit_proj.get_simulator_name() != "ghdl"

    def add_modules(
        self,
        modules: ModuleList,
        modules_no_sim: Optional[ModuleList] = None,
        include_vhdl_files: bool = True,
        include_verilog_files: bool = True,
        include_systemverilog_files: bool = True,
        **setup_vunit_kwargs: Any,
    ) -> None:
        """
        Add module source files to the VUnit project.

        Arguments:
            modules: These modules will be included in the simulation project.
            modules_no_sim: These modules will be included in the simulation project,
                but their test files will not be added.
            include_vhdl_files: Optionally disable inclusion of VHDL files from
                the modules.
            include_verilog_files: Optionally disable inclusion of Verilog files from
                the modules.
            include_systemverilog_files: Optionally disable inclusion of SystemVerilog files from
                the modules.
            setup_vunit_kwargs: Further arguments that will be sent to
                :meth:`.BaseModule.setup_vunit` for each module.
                Note that this is a "kwargs" style argument; any number of named arguments can
                be sent.
        """
        modules_no_sim = ModuleList() if modules_no_sim is None else modules_no_sim

        include_unisim = not self.args.vivado_skip
        include_ip_cores = self.has_commercial_simulator and not self.args.vivado_skip

        for module in modules + modules_no_sim:
            vunit_library = self.vunit_proj.add_library(
                library_name=module.library_name, allow_duplicate=True
            )
            simulate_this_module = module not in modules_no_sim

            for hdl_file in module.get_simulation_files(
                include_tests=simulate_this_module,
                include_unisim=include_unisim,
                include_ip_cores=include_ip_cores,
                include_vhdl_files=include_vhdl_files,
                include_verilog_files=include_verilog_files,
                include_systemverilog_files=include_systemverilog_files,
            ):
                vunit_library.add_source_file(hdl_file.path)

            if simulate_this_module:
                module.setup_vunit(
                    vunit_proj=self.vunit_proj,
                    include_unisim=include_unisim,
                    include_ip_cores=include_ip_cores,
                    inspect=self.args.inspect,
                    **setup_vunit_kwargs,
                )

    def add_vivado_simlib(self) -> Optional["VivadoSimlibCommon"]:
        """
        Add Vivado simlib to the VUnit project, unless instructed not to by ``args``.
        Will compile simlib if necessary.

        Return:
            The simlib object, ``None`` if simlib was not added due to command line argument.
        """
        if self.args.vivado_skip:
            return None

        return self._add_simlib(
            output_path=self.args.output_path_vivado, force_compile=self.args.simlib_compile
        )

    def _add_simlib(self, output_path: Path, force_compile: bool) -> "VivadoSimlibCommon":
        """
        Add Vivado simlib to the VUnit project. Compile if needed.

        .. note::

            This method can be overloaded in a subclass if you want to do something more
            advanced, e.g. fetching compiled simlib from Artifactory.

        Arguments:
            output_path: Compiled simlib will be placed in sub-directory of this path.
            force_compile: Will (re)-compile simlib even if compiled artifacts exist.

        Return:
            The simlib object.
        """
        vivado_simlib = VivadoSimlib.init(output_path=output_path, vunit_proj=self.vunit_proj)
        if force_compile or vivado_simlib.compile_is_needed:
            vivado_simlib.compile()
            vivado_simlib.to_archive()

        vivado_simlib.add_to_vunit_project()

        # Code in the "vital2000" package gives GHDL errors such as "result subtype of a pure
        # function cannot have access sub-elements". Hence, relaxed rules need to be enabled when
        # using unisim.
        self.vunit_proj.set_sim_option("ghdl.elab_flags", ["-frelaxed-rules"])

        return vivado_simlib

    def add_vivado_ip_cores(
        self,
        modules: ModuleList,
        vivado_part_name: str = "xc7z020clg400-1",
        vivado_ip_core_project_class: Optional[Type[Any]] = None,
    ) -> Optional[Path]:
        """
        Generate IP cores from the modules, unless instructed not to by ``args``.
        When running with a commercial simulator they will be added to the VUnit project.

        Arguments:
            modules: IP cores from these modules will be included in the simulation project.
            vivado_part_name: Part name to be used for Vivado IP core project.
                Might have to change from default depending on what parts you have available in your
                Vivado installation.
            vivado_ip_core_project_class: Class to be used for Vivado IP core project.
                Can be left at default in most cases.

        Return:
            Path to the Vivado IP core project's ``project`` directory.
            ``None`` if Vivado IP cores were not added due to command line argument.
        """
        if self.args.vivado_skip:
            return None

        # Generate IP core simulation files. Might be used for the vhdl_ls config,
        # even if they are not added to the simulation project.
        (
            ip_core_compile_order_file,
            ip_core_vivado_project_directory,
        ) = self._generate_ip_core_files(
            modules=modules,
            output_path=self.args.output_path_vivado,
            force_generate=self.args.ip_compile,
            part_name=vivado_part_name,
            vivado_project_class=vivado_ip_core_project_class,
        )
        if self.has_commercial_simulator:
            add_from_compile_order_file(
                vunit_obj=self.vunit_proj, compile_order_file=ip_core_compile_order_file
            )

        return ip_core_vivado_project_directory

    @staticmethod
    def _generate_ip_core_files(
        modules: ModuleList,
        output_path: Path,
        force_generate: bool,
        part_name: str,
        vivado_project_class: Optional[Type[Any]] = None,
    ) -> tuple[Path, Path]:
        """
        Generate Vivado IP core files that are to be added to the VUnit project.
        Create a new project to generate files if needed.

        Arguments:
            modules: IP cores from these modules will be included.
            output_path: IP core files will be placed in sub-directory of this path.
            force_generate: Will (re)-generate files even if they exist.
            part_name: Vivado part name.
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
                project_file=vivado_ip_cores.vivado_project_file,
                compile_order_file=vivado_ip_cores.compile_order_file,
            )

        return vivado_ip_cores.compile_order_file, vivado_ip_cores.project_directory


def create_vhdl_ls_configuration(
    output_path: Path,
    temp_files_path: Path,
    modules: ModuleList,
    ip_core_vivado_project_directory: Optional[Path] = None,
) -> None:
    """
    Create config for vhdl_ls (https://github.com/VHDL-LS/rust_hdl).
    Granted this might no be the "correct" place for this functionality.
    But since the call is somewhat quick (~10 ms), and simulate.py is run "often" it seems an
    appropriate place in order to always have an up-to-date vhdl_ls config.

    Arguments:
        output_path: Config file will be placed in this directory.
        temp_files_path: Some temporary files will be stored in a folder within this directory.
        modules: These modules will be added.
        ip_core_vivado_project_directory: Vivado IP core files in this location will be added.
    """
    # Create an empty VUnit project to add files from VUnit and OSVVM library.
    # If we were to use the "real" VUnit project that we set up above instead, all the files would
    # be in the "preprocessed" folder. Hence we use an "empty" VUnit project, and add all files
    # via modules.
    vunit_proj = VUnit.from_argv(argv=["--output-path", str(temp_files_path / "vhdl_ls_vunit_out")])
    vunit_proj.add_vhdl_builtins()
    vunit_proj.add_verification_components()
    vunit_proj.add_random()
    vunit_proj.add_osvvm()

    which_vivado = which("vivado")
    vivado_location = None if which_vivado is None else Path(which_vivado)

    tsfpga.create_vhdl_ls_config.create_configuration(
        output_path=output_path,
        modules=modules,
        vunit_proj=vunit_proj,
        vivado_location=vivado_location,
        ip_core_vivado_project_directory=ip_core_vivado_project_directory,
    )
