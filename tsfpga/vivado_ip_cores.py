# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import hashlib

from tsfpga.system_utils import create_file, delete, read_file
from tsfpga.vivado_project import VivadoProject


class VivadoIpCores:

    """
    Handle a list of IP core sources. Has a mechanism to detect whether a regenerate of IP files is needed.
    """

    _project_name = "vivado_ip_project"

    def __init__(self, modules, output_path, part_name):
        """
        Args:
            modules (list(:class:`Module <.BaseModule>`)): IP cores from  these modules will be included.
            output_path (`pathlib.Path`): The Vivado project will be placed here.
            part_name (str): Vivado part name to be used for the project.
        """
        self._project_folder = output_path.resolve() / self._project_name
        self._part_name = part_name
        self._hash_file = self._project_folder / "ip_files_hash.txt"

        self._setup(modules)

    @property
    def compile_order_file(self):
        """
        `pathlib.Path`: Path to the generated compile order file.
        """
        return self._project_folder / "compile_order.txt"

    @property
    def vivado_project_sources_directory(self):
        """
        `pathlib.Path`: Path to the "sources" directory of the Vivado project.
        """
        return self._project_folder / "vivado_ip_project.srcs" / "sources_1"

    @property
    def vivado_project_file(self):
        """
        `pathlib.Path`: Path to the Vivado project file.
        """
        return self._vivado_project.project_file(self._project_folder)

    def create_vivado_project(self):
        """
        Create IP core Vivado project.
        """
        print(f"Creating IP core project in {self._project_folder}")
        delete(self._project_folder)
        self._vivado_project.create(self._project_folder)
        self._save_hash()

    def create_vivado_project_if_needed(self):
        """
        Create IP core Vivado project if anything has changed since last time this was run.
        If

        * List of TCL files that create IP cores,
        * and contents of these files,

        is the same then it will not create. But if anything is added or removed from the list,
        or the contents of a TCL file is changed, there will be a recreation.

        Return:
            True if Vivado project was created. False otherwise.
        """
        if self._should_create():
            self.create_vivado_project()
            return True

        return False

    def _setup(self, modules):
        ip_tcl_files = []
        for module in modules:
            ip_tcl_files += module.get_ip_core_files()

        self._vivado_project = VivadoProject(
            name=self._project_name,
            modules=[],
            part=self._part_name,
            tcl_sources=ip_tcl_files
        )

        self._hash = self._calculate_hash(ip_tcl_files)

    @staticmethod
    def _calculate_hash(ip_files):
        """
        A string with hashes of the different IP core files.
        """
        data = ""

        def sort_by_file_name(path):
            return path.name

        for ip_file in sorted(ip_files, key=sort_by_file_name):
            with open(ip_file, "rb") as file_handle:
                ip_hash = hashlib.md5()
                ip_hash.update(file_handle.read())
                data += f"{ip_file}\n{ip_hash.hexdigest()}\n"

        return data

    def _save_hash(self):
        create_file(self._hash_file, self._hash)

    def _should_create(self):
        """
        Return True if a Vivado project create is needed, i.e. if anything has changed.
        """
        if not (self._hash_file.exists() and self.compile_order_file.exists()):
            return True

        return read_file(self._hash_file) != self._hash
