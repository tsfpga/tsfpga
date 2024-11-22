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
from typing import TYPE_CHECKING, Any, Optional, Type

# Third party libraries
import hdl_registers
from vunit.ui import VUnit
from vunit.vivado.vivado import add_from_compile_order_file, create_compile_order_file
from vunit.vunit_cli import VUnitCLI

# First party libraries
import tsfpga
import tsfpga.create_vhdl_ls_config
from tsfpga.git_simulation_subset import GitSimulationSubset
from tsfpga.module_list import ModuleList
from tsfpga.vivado.common import get_vivado_path
from tsfpga.vivado.ip_cores import VivadoIpCores
from tsfpga.vivado.project import VivadoIpCoreProject
from tsfpga.vivado.simlib import VivadoSimlib

if TYPE_CHECKING:
    # First party libraries
    from tsfpga.vivado.simlib_common import VivadoSimlibCommon


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
        vivado_ip_core_project_class: Optional[Type[VivadoIpCoreProject]] = None,
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
        vivado_project_class: Optional[Type[VivadoIpCoreProject]] = None,
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


class NoGitDiffTestsFound(Exception):
    """
    Raised by :meth:`.find_git_test_filters` when no tests are found due to no
    VHDL-related git diff.
    """


def find_git_test_filters(
    args: argparse.Namespace,
    repo_root: Path,
    modules: "ModuleList",
    modules_no_sim: Optional["ModuleList"] = None,
    reference_branch: str = "origin/main",
    **setup_vunit_kwargs: Any,
) -> argparse.Namespace:
    """
    Construct a VUnit test filter that will run all test cases that are affected by git changes.
    The current git state is compared to a reference branch, and differences are derived.
    See :class:`.GitSimulationSubset` for details.

    Arguments:
        args: Command line argument namespace.
        repo_root: Path to the repository root.
            Git commands will be run here.
        modules: Will be passed on to :meth:`.SimulationProject.add_modules`.
        modules_no_sim: Will be passed on to :meth:`.SimulationProject.add_modules`.
        reference_branch: The name of the reference branch that is used to collect a diff.
        setup_vunit_kwargs : Will be passed on to :meth:`.SimulationProject.add_modules`.

    Return:
        An updated argument namespace from which a VUnit project can be created.
    """
    if args.test_patterns != "*":
        raise ValueError(
            "Can not specify a test pattern when using the --vcs-minimal flag."
            f" Got {args.test_patterns}",
        )

    # Set up a dummy VUnit project that will be used for dependency scanning.
    # We could use the "real" simulation project, which the user has no doubt created, but
    # in the VUnit project there are two issues:
    # 1. It is impossible to change the test filter after the project has been created.
    # 2. We would have to access the _minimal private member.
    # Hence we create a new project here.
    # We add the 'modules_no_sim' as well as simlib, not because we need them, but to avoid
    # excessive terminal printouts about missing files in dependency scanning.
    simulation_project = SimulationProject(args=args)
    simulation_project.add_modules(
        args=args,
        modules=modules,
        modules_no_sim=modules_no_sim,
        include_verilog_files=False,
        include_systemverilog_files=False,
        **setup_vunit_kwargs,
    )
    simulation_project.add_vivado_simlib()

    testbenches_to_run = GitSimulationSubset(
        repo_root=repo_root,
        reference_branch=reference_branch,
        vunit_proj=simulation_project.vunit_proj,
        modules=modules,
    ).find_subset()

    if not testbenches_to_run:
        raise NoGitDiffTestsFound()

    # Override the test pattern argument to VUnit.
    args.test_patterns = []
    for testbench_file_name, library_name in testbenches_to_run:
        args.test_patterns.append(f"{library_name}.{testbench_file_name}.*")

    print(f"Running VUnit with test pattern {args.test_patterns}")

    # Enable minimal compilation in VUnit to save time.
    args.minimal = True

    return args


def create_vhdl_ls_configuration(
    output_path: Path,
    modules: ModuleList,
    vunit_proj: VUnit,
    ip_core_vivado_project_directory: Optional[Path] = None,
) -> None:
    """
    Create a configuration file (``vhdl_ls.toml``) for the rust_hdl VHDL Language Server
    (https://github.com/VHDL-LS/rust_hdl).

    The call is very quick (10-15 ms).
    Running it from ``simulate.py``, a script that is run "often", might be a good idea
    in order to always have an up-to-date vhdl_ls config.

    Arguments:
        output_path: Config file will be placed in this directory.
        modules: All files from these modules will be added.
        vunit_proj: All files in this VUnit project will be added.
            This includes the files from VUnit itself, and any user files.

            .. warning::
                Using a VUnit project with location/check preprocessing enabled might be
                dangerous, since it introduces the risk of editing a generated file.
        ip_core_vivado_project_directory: Vivado IP core files in this location will be added.
    """
    # Add some files needed when doing hdl-registers development.
    hdl_register_repo_root = Path(hdl_registers.__file__).parent.parent
    additional_files = [
        (hdl_register_repo_root / "tests" / "functional" / "simulation" / "*.vhd", "example"),
        (
            hdl_register_repo_root / "generated" / "vunit_out" / "generated_register" / "*.vhd",
            "example",
        ),
        (
            hdl_register_repo_root / "doc" / "sphinx" / "rst" / "generator" / "sim" / "*.vhd",
            "example",
        ),
    ]

    try:
        vivado_location = get_vivado_path()
    except FileNotFoundError:
        vivado_location = None

    tsfpga.create_vhdl_ls_config.create_configuration(
        output_path=output_path,
        modules=modules,
        vunit_proj=vunit_proj,
        files=additional_files,
        vivado_location=vivado_location,
        ip_core_vivado_project_directory=ip_core_vivado_project_directory,
    )
