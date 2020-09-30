# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import copy

from tsfpga.constraint import Constraint
from tsfpga.hdl_file import HdlFile
from tsfpga.register_list import from_toml
from tsfpga.system_utils import load_python_module


class BaseModule:
    """
    Base class for handling a HDL module with RTL code, constraints, etc.

    Files are gathered from a lot of different subfolders, to accommodate for projects having
    different catalog structure.
    """

    def __init__(self, path, library_name, default_registers=None):
        """
        Arguments:
            path (`pathlib.Path`): Path to the module folder.
            library_name (str): VHDL library name.
            default_registers (list(Register)): Default registers.
        """
        self.path = path.resolve()
        self.name = path.name
        self.library_name = library_name

        # Note: Likely mutable object, need to create deep copy before using.
        self._default_registers = default_registers
        self._registers = None

    @staticmethod
    def _get_file_list(folders, file_endings):
        """
        Returns a list of files given a list of folders.
        """
        files = []
        for folder in folders:
            for file in folder.glob("*"):
                if file.is_file() and file.name.lower().endswith(file_endings):
                    files.append(file)
        return files

    def _get_hdl_file_list(self, folders):
        """
        Return a list of HDL file objects.
        """
        return [
            HdlFile(filename) for filename in self._get_file_list(folders, HdlFile.file_endings)
        ]

    @property
    def registers(self):
        """
        :class:`.RegisterList`: Get the registers for this module.
        """
        if self._registers is not None:
            # Only create object once
            return self._registers

        toml_file = self.path / (f"regs_{self.name}.toml")
        if toml_file.exists():
            self._registers = from_toml(
                self.name, toml_file, copy.deepcopy(self._default_registers)
            )
            self.registers_hook()
            return self._registers

        for deprecated_json_file in [
            self.path / f"{self.name}_regs.json",
            self.path / f"regs_{self.name}.json",
        ]:
            if deprecated_json_file.exists():
                message = f"DEPRECATED: Using deprecated json file name: {deprecated_json_file}"
                message += f"\nDEPRECATED: Use TOML file instead: {toml_file}"
                raise ValueError(message)

        return None

    def registers_hook(self):
        """
        This function will be called directly after creating this module's registers from
        the TOML definition file.

        This is a good place if you want to add or modify some registers from Python.
        Override this method and implement the desired behavior in a child class.

        .. Note::
            This default method does nothing. Shall be overridden by modules that utilize
            this mechanism,
        """

    def create_regs_vhdl_package(self):
        """
        Create a VHDL package in this module with register definitions.
        """
        if self.registers is not None:
            self.registers.create_vhdl_package(self.path)

    def get_synthesis_files(self):
        """
        Return:
            list(:class:`.HdlFile`): Files that should be included in a synthesis project.
        """
        self.create_regs_vhdl_package()

        folders = [
            self.path,
            self.path / "src",
            self.path / "rtl",
            self.path / "hdl" / "rtl",
            self.path / "hdl" / "package",
        ]
        return self._get_hdl_file_list(folders)

    def get_simulation_files(self, include_tests=True):
        """
        Arguments:
            include_tests (bool): When False the test folder is not included.
                The use case of include_tests is when testing a primary module
                that depends on other secondary modules, we may want to compile
                the simulation files (``sim`` folder) of the secondary modules but not their
                test files (``test`` folder).

                .. Note::
                    The ``test`` files are considered private to the module and should never be used
                    by other modules.

        Return:
            list(:class:`.HdlFile`): Files that should be included in a simulation project.
        """
        self.create_regs_vhdl_package()

        test_folders = [
            self.path / "sim",
        ]

        if include_tests:
            test_folders += [self.path / "rtl" / "tb", self.path / "test"]

        return self.get_synthesis_files() + self._get_hdl_file_list(test_folders)

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

    # pylint: disable=unused-argument,no-self-use
    def setup_simulations(self, vunit_proj, **kwargs):
        print(
            "DEPRECATED: Calling deprecated BaseModule.setup_simulations(). "
            "Use BaseModule.setup_vunit() instead."
        )

    def setup_formal(self, formal_proj, **kwargs):
        """
        Setup this module's formal tests.

        .. Note::
            This default method does nothing. Should be overridden by modules that
            utilize formal verification.

        Arguments:
            formal_proj: The formal project that is being used.
            kwargs: Use this to pass an arbitrary list of arguments from your ``formal.py``
                to the module where you set up your tests. This could be, e.g., data dimensions,
                location of test files, etc.
        """

    def pre_build_hook(self, project, **kwargs):
        """
        This method will be called before an FPGA build is run. A typical use case for this
        mechanism is to set a register constant or default value based on the generics that
        are passed to the project. Could also be used to, e.g., generate BRAM init files
        based on project information, etc.

        .. Note::
            This default method does nothing. Should be overridden by modules that
            utilize this mechanism.

        Arguments:
            project (.VivadoProject): The project that is being built.
            kwargs: All parameters that are sent to the :meth:`.VivadoProject.build` method.
        """

    def get_ip_core_files(self):
        """
        Return:
            list(`pathlib.Path`): TCL files that set up the IP cores from this module.
        """
        folders = [
            self.path / "ip_cores",
        ]
        file_endings = "tcl"
        return self._get_file_list(folders, file_endings)

    def get_scoped_constraints(self):
        """
        Return:
            list(:class:`.Constraint`): Constraints that will be applied to a certain
            entity within the module.
        """
        scoped_constraints_folders = [
            self.path / "scoped_constraints",
            self.path / "entity_constraints",
            self.path / "hdl" / "constraints",
        ]
        constraints_file_endings = ("tcl", "xdc")
        constraint_files = self._get_file_list(scoped_constraints_folders, constraints_file_endings)

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

    def get_build_projects(self):  # pylint: disable=no-self-use
        """
        Get FPGA build projects defined by this module.

        .. Note::
            This default method does nothing. Should be overridden by modules that set up
            build projects.

        Return:
            list(:class:`.VivadoProject`): FPGA build projects.
        """
        return []

    @staticmethod
    def test_case_name(name=None, generics=None):
        """
        Construct a string suitable for naming test cases.

        Example result: MyName.GenericA_ValueA.GenericB_ValueB
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

    def add_config(self, test, name=None, generics=None, pre_config=None, post_check=None):
        """
        Add config for VUnit test case. Wrapper that sets a suitable name.
        """
        name = self.test_case_name(name, generics)
        test.add_config(name=name, generics=generics, pre_config=pre_config, post_check=post_check)

    def __str__(self):
        return f"{self.name}:{self.path}"


def iterate_module_folders(modules_folders):
    for modules_folder in modules_folders:
        for module_folder in modules_folder.glob("*"):
            if module_folder.is_dir():
                yield module_folder


def get_module_object(path, name, library_name_has_lib_suffix, default_registers):
    module_file = path / f"module_{name}.py"
    library_name = f"{name}_lib" if library_name_has_lib_suffix else name

    if module_file.exists():
        return load_python_module(module_file).Module(path, library_name, default_registers)
    return BaseModule(path, library_name, default_registers)


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
        modules_folders (list(`pathlib.Path`)): A list of paths where your modules are located.
        names_include (list(str)): If specified, only modules with these names will be included.
        names_avoid (list(str)): If specified, modules with these names will be discarded.
        library_name_has_lib_suffix (bool): If set, the library name will be
            ``<module name>_lib``, otherwise it is just ``<module name>``.
        default_registers (list(Register)): Default registers.

    Return:
        List of module objects (:class:`BaseModule` or child classes thereof) created from
        the specified folders.
    """
    modules = []

    for module_folder in iterate_module_folders(modules_folders):
        module_name = module_folder.name
        if (names_include is None or module_name in names_include) and (
            names_avoid is None or module_name not in names_avoid
        ):
            modules.append(
                get_module_object(
                    module_folder, module_name, library_name_has_lib_suffix, default_registers
                )
            )

    return modules
