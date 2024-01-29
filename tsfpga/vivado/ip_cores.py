# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional

# First party libraries
from tsfpga.system_utils import create_file, delete, read_file

# Local folder libraries
from .project import VivadoIpCoreProject

if TYPE_CHECKING:
    # First party libraries
    from tsfpga.ip_core_file import IpCoreFile
    from tsfpga.module_list import ModuleList

    # Local folder libraries
    from .project import VivadoProject


class VivadoIpCores:
    """
    Handle a list of IP core sources. Has a mechanism to detect whether a regenerate of IP files
    is needed.
    """

    project_name = "vivado_ip_project"

    def __init__(
        self,
        modules: "ModuleList",
        output_path: Path,
        part_name: str,
        vivado_project_class: Optional[type["VivadoProject"]] = None,
    ) -> None:
        """
        Arguments:
            modules: IP cores from  these modules will be included.
            output_path: The Vivado project will be placed here.
            part_name: Vivado part name to be used for the project.
            vivado_project_class: The Vivado project class that will be used for the IP core
                project. Is safe to leave at default in most cases.
        """
        self.project_directory = output_path.resolve() / self.project_name
        self._part_name = part_name

        vivado_project_class = (
            VivadoIpCoreProject if vivado_project_class is None else vivado_project_class
        )

        self._hash_file = self.project_directory / "ip_files_hash.txt"

        self._setup(modules, vivado_project_class)

    @property
    def compile_order_file(self) -> Path:
        """
        pathlib.Path: Path to the generated compile order file.
        """
        return self.project_directory / "compile_order.txt"

    @property
    def vivado_project_file(self) -> Path:
        """
        pathlib.Path: Path to the Vivado project file.
        """
        return self._vivado_project.project_file(self.project_directory)

    def create_vivado_project(self) -> None:
        """
        Create IP core Vivado project.
        """
        print(f"Creating IP core project in {self.project_directory}")
        delete(self.project_directory)
        success = self._vivado_project.create(self.project_directory)

        assert success, "Failed to create Vivado IP core project"

        self._save_hash()

    def create_vivado_project_if_needed(self) -> bool:
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

    def _setup(self, modules: "ModuleList", vivado_project_class: type["VivadoProject"]) -> None:
        self._vivado_project = vivado_project_class(
            name=self.project_name, modules=modules, part=self._part_name
        )

        ip_core_files = []
        for module in modules:
            # Send the same two arguments that are sent in the VivadoProject create flow
            ip_core_files += module.get_ip_core_files(generics={}, part=self._part_name)

        self._hash = self._calculate_hash(ip_core_files)

    @staticmethod
    def _calculate_hash(ip_core_files: list["IpCoreFile"]) -> str:
        """
        A string with hashes of the different IP core files.
        """
        data = ""

        def sort_by_file_name(ip_core_file: "IpCoreFile") -> str:
            return ip_core_file.path.name

        for ip_core_file in sorted(ip_core_files, key=sort_by_file_name):
            data += f"{ip_core_file.path}\n"

            if ip_core_file.variables:
                data += json.dumps(ip_core_file.variables, sort_keys=True)
                data += "\n"

            with open(ip_core_file.path, "rb") as file_handle:
                ip_hash = hashlib.md5()
                ip_hash.update(file_handle.read())
                data += f"{ip_hash.hexdigest()}\n"

        return data

    def _save_hash(self) -> None:
        create_file(self._hash_file, self._hash)

    def _should_create(self) -> bool:
        """
        Return True if a Vivado project create is needed, i.e. if anything has changed.
        """
        if not (self._hash_file.exists() and self.compile_order_file.exists()):
            return True

        return read_file(self._hash_file) != self._hash
