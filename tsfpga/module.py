# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable, Optional, Union

# Third party libraries
from hdl_registers.generator.vhdl.axi_lite.wrapper import VhdlAxiLiteWrapperGenerator
from hdl_registers.generator.vhdl.record_package import VhdlRecordPackageGenerator
from hdl_registers.generator.vhdl.register_package import VhdlRegisterPackageGenerator
from hdl_registers.generator.vhdl.simulation.check_package import (
    VhdlSimulationCheckPackageGenerator,
)
from hdl_registers.generator.vhdl.simulation.read_write_package import (
    VhdlSimulationReadWritePackageGenerator,
)
from hdl_registers.generator.vhdl.simulation.wait_until_package import (
    VhdlSimulationWaitUntilPackageGenerator,
)
from hdl_registers.parser.toml import from_toml
from hdl_registers.register import Register
from hdl_registers.register_list import RegisterList

# First party libraries
from tsfpga.constraint import Constraint
from tsfpga.hdl_file import HdlFile
from tsfpga.ip_core_file import IpCoreFile
from tsfpga.module_list import ModuleList
from tsfpga.system_utils import load_python_module

if TYPE_CHECKING:
    # Local folder libraries
    from .vivado.project import VivadoProject


class BaseModule:
    """
    Base class for handling a HDL module with RTL code, constraints, etc.

    Files are gathered from a lot of different sub-folders, to accommodate for projects having
    different catalog structure.
    """

    # Set to False if you do not want to create these register artifacts for this module.
    # Can be done in a child class or on an object instance.
    # Note that artifacts will only be created if the module actually has any registers.
    create_register_package = True
    create_record_package = True
    create_axi_lite_wrapper = True
    create_simulation_read_write_package = True
    create_simulation_check_package = True
    create_simulation_wait_until_package = True

    def __init__(
        self, path: Path, library_name: str, default_registers: Optional[list[Register]] = None
    ):
        """
        Arguments:
            path: Path to the module folder.
            library_name: VHDL library name.
            default_registers: Default registers.
        """
        self.path = path.resolve()
        self.name = path.name
        self.library_name = library_name

        self._default_registers = default_registers
        self._registers: Optional[RegisterList] = None

    @staticmethod
    def _get_file_list(
        folders: list[Path],
        file_endings: Union[str, tuple[str, ...]],
        files_include: Optional[set[Path]] = None,
        files_avoid: Optional[set[Path]] = None,
    ) -> list[Path]:
        """
        Returns a list of files given a list of folders.

        Arguments:
            folders: The folders to search.
            file_endings: File endings to include.
            files_include: Optionally filter to only include these files.
            files_avoid: Optionally filter to discard these files.
        """
        files = []
        for folder in folders:
            for file in folder.glob("*"):
                if not file.is_file():
                    continue

                if not file.name.lower().endswith(file_endings):
                    continue

                if files_include is not None and file not in files_include:
                    continue

                if files_avoid is not None and file in files_avoid:
                    continue

                files.append(file)

        return files

    def _get_hdl_file_list(  # pylint: disable=too-many-arguments
        self,
        folders: list[Path],
        files_include: Optional[set[Path]] = None,
        files_avoid: Optional[set[Path]] = None,
        include_vhdl_files: bool = True,
        include_verilog_files: bool = True,
        include_systemverilog_files: bool = True,
    ) -> list[HdlFile]:
        """
        Return a list of HDL file objects.
        """
        file_endings: tuple[str, ...] = tuple()
        if include_vhdl_files:
            file_endings += HdlFile.file_endings_mapping[HdlFile.Type.VHDL]
        if include_verilog_files:
            file_endings += HdlFile.file_endings_mapping[HdlFile.Type.VERILOG_SOURCE]
            file_endings += HdlFile.file_endings_mapping[HdlFile.Type.VERILOG_HEADER]
        if include_systemverilog_files:
            file_endings += HdlFile.file_endings_mapping[HdlFile.Type.SYSTEMVERILOG_SOURCE]
            file_endings += HdlFile.file_endings_mapping[HdlFile.Type.SYSTEMVERILOG_HEADER]

        return [
            HdlFile(path=file_path)
            for file_path in self._get_file_list(
                folders=folders,
                file_endings=file_endings,
                files_include=files_include,
                files_avoid=files_avoid,
            )
        ]

    @property
    def register_data_file(self) -> Path:
        """
        The path to this module's register data file (which may or may not exist).
        """
        return self.path / f"regs_{self.name}.toml"

    @property
    def registers(self) -> Optional[RegisterList]:
        """
        Get the registers for this module.
        Will be ``None`` if the module doesn't have any registers.
        I.e. if no TOML file exists and no hook creates registers.
        """
        if self._registers:
            # Only create object from TOML once.
            return self._registers

        toml_file = self.register_data_file
        if toml_file.exists():
            self._registers = from_toml(
                name=self.name, toml_file=toml_file, default_registers=self._default_registers
            )

        self.registers_hook()
        return self._registers

    def registers_hook(self) -> None:
        """
        This function will be called directly after creating this module's registers from
        the TOML definition file.
        If the TOML file does not exist this hook will still be called, but the module's registers
        will be ``None``.

        This is a good place if you want to add or modify some registers from Python.
        Override this method and implement the desired behavior in a subclass.

        .. Note::
            This default method does nothing.
            Shall be overridden by modules that utilize this mechanism.
        """

    def create_register_synthesis_files(self) -> None:
        """
        Create the register artifacts that are needed for synthesis.
        If this module does not have registers, this method does nothing.
        """
        if self.registers is not None:
            # Delete any old file that might exist so we don't have multiple and
            # outdated definitions.
            # This package location was used before the separate register folders were introduced,
            # back when we only created one register artifact.
            old_regs_pkg = self.path / f"{self.name}_regs_pkg.vhd"
            if old_regs_pkg.exists():
                old_regs_pkg.unlink()

            if self.create_register_package:
                VhdlRegisterPackageGenerator(
                    register_list=self.registers, output_folder=self.register_synthesis_folder
                ).create_if_needed()

            if self.create_record_package:
                VhdlRecordPackageGenerator(
                    register_list=self.registers, output_folder=self.register_synthesis_folder
                ).create_if_needed()

            if self.create_axi_lite_wrapper:
                VhdlAxiLiteWrapperGenerator(
                    register_list=self.registers, output_folder=self.register_synthesis_folder
                ).create_if_needed()

    def create_register_simulation_files(self) -> None:
        """
        Create the register artifacts that are needed for simulation.
        Does not create the implementation files, which are also technically needed for simulation.
        So a call to :meth:`.create_register_synthesis_files` must also be done.

        If this module does not have registers, this method does nothing.
        """
        if self.registers is not None:
            if self.create_simulation_read_write_package:
                VhdlSimulationReadWritePackageGenerator(
                    register_list=self.registers, output_folder=self.register_simulation_folder
                ).create_if_needed()

            if self.create_simulation_check_package:
                VhdlSimulationCheckPackageGenerator(
                    register_list=self.registers, output_folder=self.register_simulation_folder
                ).create_if_needed()

            if self.create_simulation_wait_until_package:
                VhdlSimulationWaitUntilPackageGenerator(
                    register_list=self.registers, output_folder=self.register_simulation_folder
                ).create_if_needed()

    @property
    def synthesis_folders(self) -> list[Path]:
        """
        Synthesis/implementation source code files will be gathered from these folders.
        """
        return [
            self.path,
            self.path / "src",
            self.path / "rtl",
            self.path / "hdl" / "rtl",
            self.path / "hdl" / "package",
            self.register_synthesis_folder,
        ]

    @property
    def register_synthesis_folder(self) -> Path:
        """
        Generated register artifacts that are needed for synthesis/implementation will be
        placed in this folder.
        """
        return self.path / "regs_src"

    @property
    def sim_folders(self) -> list[Path]:
        """
        Files with simulation models (the ``sim`` folder) will be gathered from these folders.
        """
        return [
            self.path / "sim",
            self.register_simulation_folder,
        ]

    @property
    def register_simulation_folder(self) -> Path:
        """
        Generated register artifacts that are needed for simulation will be placed in this folder.
        """
        return self.path / "regs_sim"

    @property
    def test_folders(self) -> list[Path]:
        """
        Testbench files will be gathered from these folders.
        """
        return [
            self.path / "test",
            self.path / "rtl" / "tb",
        ]

    def get_synthesis_files(  # pylint: disable=unused-argument
        self,
        files_include: Optional[set[Path]] = None,
        files_avoid: Optional[set[Path]] = None,
        include_vhdl_files: bool = True,
        include_verilog_files: bool = True,
        include_systemverilog_files: bool = True,
        **kwargs: Any,
    ) -> list[HdlFile]:
        """
        Get a list of files that shall be included in a synthesis project.

        The ``files_include`` and ``files_avoid`` arguments can be used to filter what files are
        included.
        This can be useful in many situations, e.g. when encrypted files of files that include an
        IP core shall be avoided.
        It is recommended to overload this function in a subclass in your ``module_*.py``,
        and call this super method with the arguments supplied.

        Arguments:
            files_include: Optionally filter to only include these files.
            files_avoid: Optionally filter to discard these files.
            include_vhdl_files: Optionally disable inclusion of files with VHDL
                file endings.
            include_verilog_files: Optionally disable inclusion of files with Verilog
                file endings.
            include_systemverilog_files: Optionally disable inclusion of files with SystemVerilog
                file endings.
            kwargs: Further parameters that can be sent by build flow to control what
                files are included.

        Return:
            Files that should be included in a synthesis project.
        """
        self.create_register_synthesis_files()

        return self._get_hdl_file_list(
            folders=self.synthesis_folders,
            files_include=files_include,
            files_avoid=files_avoid,
            include_vhdl_files=include_vhdl_files,
            include_verilog_files=include_verilog_files,
            include_systemverilog_files=include_systemverilog_files,
        )

    def get_simulation_files(  # pylint: disable=too-many-arguments
        self,
        include_tests: bool = True,
        files_include: Optional[set[Path]] = None,
        files_avoid: Optional[set[Path]] = None,
        include_vhdl_files: bool = True,
        include_verilog_files: bool = True,
        include_systemverilog_files: bool = True,
        **kwargs: Any,
    ) -> list[HdlFile]:
        """
        See :meth:`.get_synthesis_files` for instructions on how to use ``files_include``
        and ``files_avoid``.

        Arguments:
            include_tests: When ``False``, the ``test`` files are not included
                (the ``sim`` files are always included).
            files_include: Optionally filter to only include these files.
            files_avoid: Optionally filter to discard these files.
            include_vhdl_files: Optionally disable inclusion of files with VHDL
                file endings.
            include_verilog_files: Optionally disable inclusion of files with Verilog
                file endings.
            include_systemverilog_files: Optionally disable inclusion of files with SystemVerilog
                file endings.
            kwargs: Further parameters that can be sent by simulation flow to control what
                files are included.

        Return:
            Files that should be included in a simulation project.
        """
        # Shallow copy the list since we might append to it.
        sim_and_test_folders = self.sim_folders.copy()

        if include_tests:
            sim_and_test_folders += self.test_folders

        self.create_register_simulation_files()

        test_files = self._get_hdl_file_list(
            folders=sim_and_test_folders,
            files_include=files_include,
            files_avoid=files_avoid,
            include_vhdl_files=include_vhdl_files,
            include_verilog_files=include_verilog_files,
            include_systemverilog_files=include_systemverilog_files,
        )

        synthesis_files = self.get_synthesis_files(
            files_include=files_include,
            files_avoid=files_avoid,
            include_vhdl_files=include_vhdl_files,
            include_verilog_files=include_verilog_files,
            include_systemverilog_files=include_systemverilog_files,
            **kwargs,
        )

        return synthesis_files + test_files

    def get_documentation_files(  # pylint: disable=unused-argument
        self,
        files_include: Optional[set[Path]] = None,
        files_avoid: Optional[set[Path]] = None,
        include_vhdl_files: bool = True,
        include_verilog_files: bool = True,
        include_systemverilog_files: bool = True,
        **kwargs: Any,
    ) -> list[HdlFile]:
        """
        Get a list of files that shall be included in a documentation build.

        It will return all files from the module except testbenches and any generated
        register package.
        Overwrite in a subclass if you want to change this behavior.

        Arguments:
            files_include: Optionally filter to only include these files.
            files_avoid: Optionally filter to discard these files.
            include_vhdl_files: Optionally disable inclusion of files with VHDL
                file endings.
            include_verilog_files: Optionally disable inclusion of files with Verilog
                file endings.
            include_systemverilog_files: Optionally disable inclusion of files with SystemVerilog
                file endings.

        Return:
            Files that should be included in documentation.
        """
        # Do not include generated register code in the documentation.
        files_to_avoid = set(
            self._get_file_list(
                folders=[self.register_synthesis_folder, self.register_simulation_folder],
                file_endings="vhd",
            )
        )
        if files_avoid:
            files_to_avoid |= files_avoid

        return self._get_hdl_file_list(
            folders=self.synthesis_folders + self.sim_folders,
            files_include=files_include,
            files_avoid=files_to_avoid,
            include_vhdl_files=include_vhdl_files,
            include_verilog_files=include_verilog_files,
            include_systemverilog_files=include_systemverilog_files,
        )

    # pylint: disable=unused-argument
    def get_ip_core_files(
        self,
        files_include: Optional[set[Path]] = None,
        files_avoid: Optional[set[Path]] = None,
        **kwargs: Any,
    ) -> list[IpCoreFile]:
        """
        Get IP cores for this module.

        Note that the :class:`.ip_core_file.IpCoreFile` class accepts a ``variables`` argument that
        can be used to parameterize IP core creation. By overloading this method in a subclass
        you can pass on ``kwargs`` arguments from the build/simulation flow to
        :class:`.ip_core_file.IpCoreFile` creation to achieve this parameterization.

        Arguments:
            files_include: Optionally filter to only include these files.
            files_avoid: Optionally filter to discard these files.
            kwargs: Further parameters that can be sent by build/simulation flow to control what
                IP cores are included and what their variables are.

        Return:
            The IP cores for this module.
        """
        folders = [
            self.path / "ip_cores",
        ]
        file_endings = "tcl"
        return [
            IpCoreFile(ip_core_file)
            for ip_core_file in self._get_file_list(
                folders=folders,
                file_endings=file_endings,
                files_include=files_include,
                files_avoid=files_avoid,
            )
        ]

    # pylint: disable=unused-argument
    def get_scoped_constraints(
        self,
        files_include: Optional[set[Path]] = None,
        files_avoid: Optional[set[Path]] = None,
        **kwargs: Any,
    ) -> list[Constraint]:
        """
        Constraints that shall be applied to a certain entity within this module.

        Arguments:
            files_include: Optionally filter to only include these files.
            files_avoid: Optionally filter to discard these files.
            kwargs: Further parameters that can be sent by build/simulation flow to control what
                constraints are included.

        Return:
            The constraints.
        """
        folders = [
            self.path / "scoped_constraints",
            self.path / "entity_constraints",
            self.path / "hdl" / "constraints",
        ]
        file_endings = ("tcl", "xdc")
        constraint_files = self._get_file_list(
            folders=folders,
            file_endings=file_endings,
            files_include=files_include,
            files_avoid=files_avoid,
        )

        constraints = []
        if constraint_files:
            synthesis_files = self.get_synthesis_files()
            for constraint_file in constraint_files:
                # Scoped constraints often depend on clocks having been created by another
                # constraint file before they can work. Set processing order to "late" to make
                # this more probable.
                constraint = Constraint(
                    constraint_file, scoped_constraint=True, processing_order="late"
                )
                constraint.validate_scoped_entity(synthesis_files)
                constraints.append(constraint)

        return constraints

    def setup_vunit(self, vunit_proj: Any, **kwargs: Any) -> None:
        """
        Setup local configuration of this module's test benches.

        .. Note::
            This default method does nothing. Should be overridden by modules that have
            any test benches that operate via generics.

        Arguments:
            vunit_proj: The VUnit project that is used to run simulation.
            kwargs: Use this to pass an arbitrary list of arguments from your ``simulate.py``
                to the module where you set up your tests. This could be, e.g., data dimensions,
                location of test files, etc.
        """

    def pre_build(
        self, project: "VivadoProject", **kwargs: Any
    ) -> bool:  # pylint: disable=unused-argument
        """
        This method hook will be called before an FPGA build is run. A typical use case for this
        mechanism is to set a register constant or default value based on the generics that
        are passed to the project. Could also be used to, e.g., generate BRAM init files
        based on project information, etc.

        .. Note::
            This default method does nothing. Should be overridden by modules that
            utilize this mechanism.

        Arguments:
            project: The project that is being built.
            kwargs: All other parameters to the build flow. Includes arguments to
                :meth:`.VivadoProject.build` method as well as other arguments set in
                :meth:`.VivadoProject.__init__`.

        Return:
            True if everything went well.
        """
        return True

    def get_build_projects(self) -> list["VivadoProject"]:
        """
        Get FPGA build projects defined by this module.

        .. Note::
            This default method does nothing. Should be overridden by modules that set up
            build projects.

        Return:
            FPGA build projects.
        """
        return []

    @staticmethod
    def test_case_name(
        name: Optional[str] = None, generics: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Construct a string suitable for naming test cases.

        Arguments:
            name: Optional base name.
            generics: Dictionary of values that will be included in the name.

        Return:
            For example ``MyBaseName.GenericA_ValueA.GenericB_ValueB``.
        """
        if name:
            test_case_name = name
        else:
            test_case_name = ""

        if generics:
            generics_string = ".".join([f"{key}_{value}" for key, value in generics.items()])

            if test_case_name:
                test_case_name = f"{name}.{generics_string}"
            else:
                test_case_name = generics_string

        return test_case_name

    def add_vunit_config(  # pylint: disable=too-many-arguments
        self,
        test: Any,
        name: Optional[str] = None,
        generics: Optional[dict[str, Any]] = None,
        set_random_seed: Optional[Union[bool, int]] = False,
        pre_config: Optional[Callable[..., bool]] = None,
        post_check: Optional[Callable[..., bool]] = None,
    ) -> None:
        """
        Add config for VUnit test case.
        Wrapper that sets a suitable name and can set a random seed generic.

        Arguments:
            test: VUnit test object. Can be testbench or test case.
            name: Optional designated name for this config. Will be used to form the name of
                the config together with the ``generics`` value.
            generics: Generic values that will be applied to the testbench entity. The values
                will also be used to form the name of the config.
            set_random_seed: Controls setting of the ``seed`` generic:

                * When this argument is not assigned, or assigned ``False``, the generic will not
                  be set.
                * When set to boolean ``True``, a random natural (non-negative integer)
                  generic value will be set.
                * When set to an integer value, that value will be set for the generic.
                  This is useful to get a static test case name for waveform inspection.

                If the generic is to be set it must exist in the testbench entity, and should have
                VHDL type ``natural``.
            pre_config: Function to be run before the test.
                See `VUnit documentation <https://vunit.github.io/py/ui.html>`_ for details.
            post_check: Function to be run after the test.
                See `VUnit documentation <https://vunit.github.io/py/ui.html>`_ for details.
        """
        generics = {} if generics is None else generics

        # Note that "bool" is a sub-class of "int" in python, so isinstance(set_random_seed, int)
        # returns True if it is an integer or a bool.
        if isinstance(set_random_seed, bool):
            if set_random_seed:
                # Use the maximum range for a natural in VHDL-2008
                generics["seed"] = random.randint(0, 2**31 - 1)

        elif isinstance(set_random_seed, int):
            generics["seed"] = set_random_seed

        name = self.test_case_name(name=name, generics=generics)
        # VUnit does not allow an empty name, which can happen if both 'name' and 'generics' to
        # this method are None, but the user sets for example a 'pre_config'.
        # Avoid this error mode by setting a default name when it happens.
        name = "test" if name == "" else name

        test.add_config(name=name, generics=generics, pre_config=pre_config, post_check=post_check)

    def __str__(self) -> str:
        return f"{self.name}:{self.path}"


def get_modules(
    modules_folder: Optional[Path] = None,
    modules_folders: Optional[list[Path]] = None,
    names_include: Optional[set[str]] = None,
    names_avoid: Optional[set[str]] = None,
    library_name_has_lib_suffix: bool = False,
    default_registers: Optional[list[Register]] = None,
) -> ModuleList:
    """
    Get a list of module objects (:class:`BaseModule` or subclasses thereof) based on the source
    code folders.

    Arguments:
        modules_folder: The path to the folder containing modules.
        modules_folders: Optionally, you can specify many folders with modules that will all
            be searched.
        names_include: If specified, only modules with these names will be included.
        names_avoid: If specified, modules with these names will be discarded.
        library_name_has_lib_suffix: If set, the library name will be ``<module name>_lib``,
            otherwise it is just ``<module name>``.
        default_registers: Default registers.

    Return:
        The modules created from the specified folders.
    """
    modules = ModuleList()

    folders = []
    if modules_folder is not None:
        folders.append(modules_folder)
    if modules_folders is not None:
        folders += modules_folders

    for module_folder in _iterate_module_folders(folders):
        module_name = module_folder.name

        if names_include is not None and module_name not in names_include:
            continue

        if names_avoid is not None and module_name in names_avoid:
            continue

        modules.append(
            _get_module_object(
                path=module_folder,
                name=module_name,
                library_name_has_lib_suffix=library_name_has_lib_suffix,
                default_registers=default_registers,
            )
        )

    return modules


def get_module(
    name: str,
    modules_folder: Optional[Path] = None,
    modules_folders: Optional[list[Path]] = None,
    library_name_has_lib_suffix: bool = False,
    default_registers: Optional[list[Register]] = None,
) -> BaseModule:
    """
    Get a single module object, for a module found in one of the specified source code folders.
    Is a wrapper around :func:`.get_modules`.

    Arguments:
        name: The name of the module.
        modules_folder: The path to the folder containing modules.
        modules_folders: Optionally, you can specify many folders with modules that will all
            be searched.
        library_name_has_lib_suffix: If set, the library name will be ``<module name>_lib``,
            otherwise it is just ``<module name>``.
        default_registers: Default registers.

    Return:
        The requested module.
    """
    modules = get_modules(
        modules_folder=modules_folder,
        modules_folders=modules_folders,
        names_include={name},
        library_name_has_lib_suffix=library_name_has_lib_suffix,
        default_registers=default_registers,
    )

    if not modules:
        raise RuntimeError(f'Could not find module "{name}".')

    if len(modules) > 1:
        raise RuntimeError(f'Found multiple modules named "{name}".')

    return modules[0]


def _iterate_module_folders(modules_folders: list[Path]) -> Iterable[Path]:
    for modules_folder in modules_folders:
        for module_folder in modules_folder.glob("*"):
            if module_folder.is_dir():
                yield module_folder


def _get_module_object(
    path: Path,
    name: str,
    library_name_has_lib_suffix: bool,
    default_registers: Optional[list["Register"]],
) -> BaseModule:
    module_file = path / f"module_{name}.py"
    library_name = f"{name}_lib" if library_name_has_lib_suffix else name

    if module_file.exists():
        # We assume that the user lets their 'Module' class inherit from 'BaseModule'.
        module: BaseModule = load_python_module(module_file).Module(
            path=path,
            library_name=library_name,
            default_registers=default_registers,
        )
        return module

    return BaseModule(path=path, library_name=library_name, default_registers=default_registers)
