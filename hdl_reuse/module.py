from glob import glob
from os.path import basename, isfile, join, exists, isdir

from hdl_reuse.constraints import Constraint
from hdl_reuse.system_utils import load_python_module


class BaseModule:
    """
    Base class for handling a HDL module.
    """

    _source_code_file_endings = ("vhd", "v")

    def __init__(self, path, library_name_has_lib_suffix=False):
        self.path = path
        self.name = basename(self.path)
        self._library_name_has_lib_suffix = library_name_has_lib_suffix

    def _get_source_code_files_from_folders(self, folders):
        """
        Returns a list of files given a list of folders.
        """
        files = []
        for folder in folders:
            for file in glob(join(folder, "*")):
                if isfile(file) and file.lower().endswith(self._source_code_file_endings):
                    files.append(file)
        return files

    def get_synthesis_files(self):
        """
        List of files that should be included in a synthesis project.
        """
        folders = [self.path]
        return self._get_source_code_files_from_folders(folders)

    def get_simulation_files(self):
        """
        List of files that should be included in a simulation project.
        """
        folders = [self.path, join(self.path, "test")]
        return self._get_source_code_files_from_folders(folders)

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
        pass

    def get_entity_constraints(self):
        """
        Get a list of constraints that will be applied to a certain entity within the module.
        """
        entity_constraints = []
        for file in glob(join(self.path, "entity_constraints", "*.tcl")):
            entity_constraints.append(Constraint(file, entity_level_constraint=True))
        return entity_constraints

    def __str__(self):
        return self.name + ": " + self.path


def iterate_module_folders(modules_folders):
    for modules_folder in modules_folders:
        for module_folder in glob(join(modules_folder, "*")):
            if isdir(module_folder):
                yield module_folder


def get_module_object(path, name):
    module_file = join(path, "module_" + name + ".py")

    if exists(module_file):
        return load_python_module(module_file).Module(path)
    return BaseModule(path)


def get_modules(modules_folders, names=None):
    modules = []

    for module_folder in iterate_module_folders(modules_folders):
        module_name = basename(module_folder)
        if names is None or module_name in names:
            modules.append(get_module_object(module_folder, module_name))

    return modules
