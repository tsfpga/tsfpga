# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from glob import glob
from os.path import basename, isfile, join, exists, isdir

from tsfpga.system_utils import load_python_module
from tsfpga.constraint import Constraint
from tsfpga.registers import from_json, get_default_registers


class BaseModule:
    """
    Base class for handling a HDL module with RTL code, constraints, etc.

    Files are gathered from a lot of different subfolders, to accomodate for projects having different catalog structure.
    """

    _hdl_file_endings = ("vhd", "v")

    def __init__(self, path, library_name_has_lib_suffix=False):
        self.path = path
        self.name = basename(self.path)
        self._library_name_has_lib_suffix = library_name_has_lib_suffix
        self._registers = None

    @staticmethod
    def _get_file_list(folders, file_endings):
        """
        Returns a list of files given a list of folders.
        """
        files = []
        for folder in folders:
            for file in glob(join(folder, "*")):
                if isfile(file) and file.lower().endswith(file_endings):
                    files.append(file)
        return files

    @property
    def registers(self):
        if self._registers is not None:
            # Only create object once
            return self._registers

        json_file = join(self.path, self.name + "_regs.json")
        if exists(json_file):
            self._registers = from_json(self.name, json_file, get_default_registers())
            return self._registers

    def _create_regs_vhdl_package(self):
        if self.registers is not None:
            pkg_file = join(self.path, self.name + "_regs_pkg.vhd")
            self.registers.create_vhdl_package(pkg_file)

    def get_synthesis_files(self):
        """
        List of files that should be included in a synthesis project.
        """
        self._create_regs_vhdl_package()

        folders = [
            self.path,
            join(self.path, "hdl", "rtl"),
            join(self.path, "hdl", "package"),
        ]
        return self._get_file_list(folders, self._hdl_file_endings)

    def get_simulation_files(self, include_tests=True):
        """
        List of files that should be included in a simulation project.

        When include_tests is False the test folder is not included.
        The use case of include_tests is when testing a primary module
        that depends on other secondary modules we may want to compile
        the simulation files of the secondary modules but not their
        test files.

        Note: test-files are considered private to the module and
        should never be used by other modules.
        """
        self._create_regs_vhdl_package()

        test_folders = [
            join(self.path, "sim"),
        ]

        if include_tests:
            test_folders += [join(self.path, "rtl", "tb"),
                             join(self.path, "test")]

        return self.get_synthesis_files() + self._get_file_list(test_folders, self._hdl_file_endings)

    @property
    def library_name(self):
        """
        Some think library name should be <module_name>_lib.
        It actually shouldn't since built in VHDL libraries are named e.g. ieee not ieee_lib.
        But we keep the functionality for legacy reasons.
        """
        if self._library_name_has_lib_suffix:
            return self.name + "_lib"
        return self.name

    def setup_simulations(self, vunit_proj, **kwargs):
        """
        Setup local configuration of this module's test benches.
        Should be overriden by modules that have any test benches that operate via generics.
        """

    def get_ip_core_files(self):
        """
        Get a list of TCL files that set up the IP cores from this module.
        """
        folders = [
            join(self.path, "ip_cores"),
        ]
        file_endings = ("tcl")
        return self._get_file_list(folders, file_endings)

    def get_scoped_constraints(self):
        """
        Get a list of constraints that will be applied to a certain entity within the module.
        """
        scoped_constraints_folders = [
            join(self.path, "scoped_constraints"),
            join(self.path, "entity_constraints"),
            join(self.path, "hdl", "constraints"),
        ]
        constraints_file_endings = ("tcl", "xdc")
        constraint_files = self._get_file_list(scoped_constraints_folders, constraints_file_endings)

        constraints = []
        for file in constraint_files:
            constraints.append(Constraint(file, scoped_constraint=True))
        return constraints

    def __str__(self):
        return self.name + ": " + self.path


def iterate_module_folders(modules_folders):
    for modules_folder in modules_folders:
        for module_folder in glob(join(modules_folder, "*")):
            if isdir(module_folder):
                yield module_folder


def get_module_object(path, name, library_name_has_lib_suffix):
    module_file = join(path, "module_" + name + ".py")

    if exists(module_file):
        return load_python_module(module_file).Module(path, library_name_has_lib_suffix)
    return BaseModule(path, library_name_has_lib_suffix)


def get_modules(modules_folders, names=None, library_name_has_lib_suffix=False):
    modules = []

    for module_folder in iterate_module_folders(modules_folders):
        module_name = basename(module_folder)
        if names is None or module_name in names:
            modules.append(get_module_object(module_folder, module_name, library_name_has_lib_suffix))

    return modules
