# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import random

# Third party libraries
from hdl_registers.parser import from_toml

# First party libraries
from tsfpga.constraint import Constraint
from tsfpga.hdl_file import HdlFile
from tsfpga.ip_core_file import IpCoreFile
from tsfpga.module_list import ModuleList
from tsfpga.system_utils import load_python_module


class BaseModule:
    """
    Base class for handling a HDL module with RTL code, constraints, etc.

    Files are gathered from a lot of different sub-folders, to accommodate for projects having
    different catalog structure.
    """

    def __init__(self, path, library_name, default_registers=None):
        """
        Arguments:
            path (pathlib.Path): Path to the module folder.
            library_name (str): VHDL library name.
            default_registers (list(hdl_registers.register.Register)): Default registers.
        """
        self.path = path.resolve()
        self.name = path.name
        self.library_name = library_name

        self._default_registers = default_registers
        self._registers = None

    @staticmethod
    def _get_file_list(folders, file_endings, files_include=None, files_avoid=None):
        """
        Returns a list of files given a list of folders.

        Arguments:
            folders (pathlib.Path): The folders to search.
            file_endings (tuple(str)): File endings to include.
            files_include (set(pathlib.Path)): Optionally filter to only include these files.
            files_avoid (set(pathlib.Path)): Optionally filter to discard these files.
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

    def _get_hdl_file_list(self, folders, files_include=None, files_avoid=None):
        """
        Return a list of HDL file objects.
        """
        return [
            HdlFile(file_path)
            for file_path in self._get_file_list(
                folders=folders,
                file_endings=HdlFile.file_endings,
                files_include=files_include,
                files_avoid=files_avoid,
            )
        ]

    @property
    def registers(self):
        """
        hdl_registers.register_list.RegisterList: Get the registers for this module. Can be
            ``None`` if no TOML file exists and no hook creates registers.
        """
        if self._registers is not None:
            # Only create object once
            return self._registers

        toml_file = self.path / f"regs_{self.name}.toml"
        if toml_file.exists():
            self._registers = from_toml(self.name, toml_file, self._default_registers)

        self.registers_hook()
        return self._registers

    def registers_hook(self):
        """
        This function will be called directly after creating this module's registers from
        the TOML definition file. If the TOML file does not exist this hook will still be called,
        but the module's registers will be ``None``.

        This is a good place if you want to add or modify some registers from Python.
        Override this method and implement the desired behavior in a child class.

        .. Note::
            This default method does nothing. Shall be overridden by modules that utilize
            this mechanism.
        """

    def create_regs_vhdl_package(self):
        """
        Create a VHDL package in this module with register definitions.
        """
        if self.registers is not None:
            self.registers.create_vhdl_package(self.path)

    @property
    def synthesis_folders(self):
        """
        Synthesis/implementation source code files will be gathered from these folders.

        Return:
            list(pathlib.Path): Folder paths.
        """
        return [
            self.path,
            self.path / "src",
            self.path / "rtl",
            self.path / "hdl" / "rtl",
            self.path / "hdl" / "package",
        ]

    @property
    def sim_folders(self):
        """
        Files with simulation models (the ``sim`` folder) will be gathered from these folders.

        Return:
            list(pathlib.Path): Folder paths.
        """
        return [
            self.path / "sim",
        ]

    @property
    def test_folders(self):
        """
        Testbench files will be gathered from these folders.

        Return:
            list(pathlib.Path): Folder paths.
        """
        return [
            self.path / "test",
            self.path / "rtl" / "tb",
        ]

    def get_synthesis_files(
        self, files_include=None, files_avoid=None, **kwargs
    ):  # pylint: disable=unused-argument
        """
        Get a list of files that shall be included in a synthesis project.

        The ``files_include`` and ``files_avoid`` arguments can be used to filter what files are
        included.
        This can be useful in many situations, e.g. when encrypted files of files that include an
        IP core shall be avoided.
        It is recommended to overload this function in a child class in your ``module_*.py``,
        and call this super method with the arguments supplied.

        Arguments:
            files_include (set(`pathlib.Path`)): Optionally filter to only include these files.
            files_avoid (set(`pathlib.Path`)): Optionally filter to discard these files.
            kwargs: Further parameters that can be sent by build flow to control what
                files are included.

        Return:
            list(HdlFile): Files that should be included in a synthesis project.
        """
        self.create_regs_vhdl_package()

        return self._get_hdl_file_list(
            folders=self.synthesis_folders, files_include=files_include, files_avoid=files_avoid
        )

    def get_simulation_files(
        self, include_tests=True, files_include=None, files_avoid=None, **kwargs
    ):
        """
        See :meth:`.get_synthesis_files` for instructions on how to use ``files_include``
        and ``files_avoid``.

        Arguments:
            include_tests (bool): When ``False``, the ``test`` files are not included
                (the ``sim`` files are always included).
            files_include (set(`pathlib.Path`)): Optionally filter to only include these files.
            files_avoid (set(`pathlib.Path`)): Optionally filter to discard these files.
            kwargs: Further parameters that can be sent by simulation flow to control what
                files are included.

        Return:
            list(HdlFile): Files that should be included in a simulation project.
        """
        test_folders = self.sim_folders.copy()

        if include_tests:
            test_folders += self.test_folders

        test_files = self._get_hdl_file_list(
            folders=test_folders, files_include=files_include, files_avoid=files_avoid
        )

        synthesis_files = self.get_synthesis_files(
            files_include=files_include, files_avoid=files_avoid, **kwargs
        )

        return synthesis_files + test_files

    def get_documentation_files(
        self, files_include=None, files_avoid=None, **kwargs
    ):  # pylint: disable=unused-argument
        """
        Get a list of files that shall be included in a documentation build.

        It will return all files from the module except testbenches and any generated
        register package.
        Overwrite in a child class if you want to change this behavior.

        Return:
            list(HdlFile): Files that should be included in documentation.
        """
        return self._get_hdl_file_list(
            folders=self.synthesis_folders + self.sim_folders,
            files_include=files_include,
            files_avoid=files_avoid,
        )

    # pylint: disable=unused-argument
    def get_ip_core_files(self, files_include=None, files_avoid=None, **kwargs):
        """
        Get IP cores for this module.

        Note that the :class:`.ip_core_file.IpCoreFile` class accepts a ``variables`` argument that
        can be used to parameterize IP core creation. By overloading this method in a child class
        you can pass on ``kwargs`` arguments from the build/simulation flow to
        :class:`.ip_core_file.IpCoreFile` creation to achieve this parameterization.

        Arguments:
            files_include (set(`pathlib.Path`)): Optionally filter to only include these files.
            files_avoid (set(`pathlib.Path`)): Optionally filter to discard these files.
            kwargs: Further parameters that can be sent by build/simulation flow to control what
                IP cores are included and what their variables are.

        Return:
            list(IpCoreFile): The IP cores for this module.
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
    def get_scoped_constraints(self, files_include=None, files_avoid=None, **kwargs):
        """
        Constraints that shall be applied to a certain entity within this module.

        Arguments:
            files_include (set(`pathlib.Path`)): Optionally filter to only include these files.
            files_avoid (set(`pathlib.Path`)): Optionally filter to discard these files.
            kwargs: Further parameters that can be sent by build/simulation flow to control what
                constraints are included.

        Return:
            list(Constraint): The constraints.
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

    def setup_vunit(self, vunit_proj, **kwargs):
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

    def pre_build(self, project, **kwargs):  # pylint: disable=unused-argument
        """
        This method hook will be called before an FPGA build is run. A typical use case for this
        mechanism is to set a register constant or default value based on the generics that
        are passed to the project. Could also be used to, e.g., generate BRAM init files
        based on project information, etc.

        .. Note::
            This default method does nothing. Should be overridden by modules that
            utilize this mechanism.

        Arguments:
            project (VivadoProject): The project that is being built.
            kwargs: All other parameters to the build flow. Includes arguments to
                :meth:`.VivadoProject.build` method as well as other arguments set in
                :meth:`.VivadoProject.__init__`.

        Return:
            bool: True if everything went well.
        """
        return True

    def get_build_projects(self):
        """
        Get FPGA build projects defined by this module.

        .. Note::
            This default method does nothing. Should be overridden by modules that set up
            build projects.

        Return:
            list(VivadoProject): FPGA build projects.
        """
        return []

    @staticmethod
    def test_case_name(name=None, generics=None):
        """
        Construct a string suitable for naming test cases.

        Arguments:
            name (str): Optional base name.
            generics (dict): Dictionary of values that will be included in the name.

        Returns:
            str: For example ``MyBaseName.GenericA_ValueA.GenericB_ValueB``.
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

    def add_vunit_config(
        self,
        test,
        name=None,
        generics=None,
        set_random_seed=False,
        pre_config=None,
        post_check=None,
    ):  # pylint: disable=too-many-arguments
        """
        Add config for VUnit test case. Wrapper that sets a suitable name and can set a random
        seed generic.

        Arguments:
            test: VUnit test object. Can be testbench or test case.
            name (str): Optional designated name for this config. Will be used to form the name of
                the config together with the ``generics`` value.
            generics (dict): Generic values that will be applied to the testbench entity. The values
                will also be used to form the name of the config.
            set_random_seed (bool, int): Controls setting of the ``seed`` generic:

                * When this argument is not assigned, or assigned ``False``, the generic will not
                  be set.
                * When set to boolean ``True``, a random natural (non-negative integer)
                  generic value will be set.
                * When set to an integer value, that value will be set for the generic.
                  This is useful to get a static test case name for waveform inspection.

                If the generic is to be set it must exist in the testbench entity, and should have
                VHDL type ``natural``.
            pre_config: Function to be run before the test. See VUnit documentation for details.
            post_check: Function to be run after the test. See VUnit documentation for details.
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

        name = self.test_case_name(name, generics)
        test.add_config(name=name, generics=generics, pre_config=pre_config, post_check=post_check)

    def __str__(self):
        return f"{self.name}:{self.path}"


def get_modules(
    modules_folders,
    names_include=None,
    names_avoid=None,
    library_name_has_lib_suffix=False,
    default_registers=None,
):
    """
    Get a list of Module objects based on the source code folders.

    Arguments:
        modules_folders (list(pathlib.Path)): A list of paths where your modules are located.
        names_include (list(str)): If specified, only modules with these names will be included.
        names_avoid (list(str)): If specified, modules with these names will be discarded.
        library_name_has_lib_suffix (bool): If set, the library name will be
            ``<module name>_lib``, otherwise it is just ``<module name>``.
        default_registers (list(hdl_registers.register.Register)): Default registers.

    Return:
        ModuleList: List of module objects (:class:`BaseModule` or child classes thereof)
        created from the specified folders.
    """
    modules = ModuleList()

    for module_folder in _iterate_module_folders(modules_folders):
        module_name = module_folder.name

        if names_include is not None and module_name not in names_include:
            continue

        if names_avoid is not None and module_name in names_avoid:
            continue

        modules.append(
            _get_module_object(
                module_folder, module_name, library_name_has_lib_suffix, default_registers
            )
        )

    return modules


def _iterate_module_folders(modules_folders):
    for modules_folder in modules_folders:
        for module_folder in modules_folder.glob("*"):
            if module_folder.is_dir():
                yield module_folder


def _get_module_object(path, name, library_name_has_lib_suffix, default_registers):
    module_file = path / f"module_{name}.py"
    library_name = f"{name}_lib" if library_name_has_lib_suffix else name

    if module_file.exists():
        return load_python_module(module_file).Module(path, library_name, default_registers)
    return BaseModule(path, library_name, default_registers)
