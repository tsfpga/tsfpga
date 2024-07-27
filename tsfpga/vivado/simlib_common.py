# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import platform
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from shutil import make_archive
from typing import Optional

# First party libraries
from tsfpga.system_utils import create_file, delete
from tsfpga.vivado.common import get_vivado_version

# Local folder libraries
from .common import get_vivado_path


class VivadoSimlibCommon(ABC):
    """
    Class for handling Vivado simlib used for simulation. Keeps track of when a
    (re)compile is needed.

    This is a base class that defines an interface and some common methods.
    See subclasses for details: :class:`.VivadoSimlibGhdl`, :class:`.VivadoSimlibCommercial`.
    """

    # The version of this class. Can be bumped to force a re-compile if e.g. the TCL script changes
    # or the output folder structure is updated.
    _format_version_id = 4

    # Set in subclass to a list of strings. The libraries that shall be compiled and added to
    # VUnit project.
    library_names: list[str]

    def __init__(self, vivado_path: Optional[Path], output_path: Path) -> None:
        """
        Call from subclass. Please do not instantiate this class directly.
        """
        self._vivado_path = get_vivado_path(vivado_path)
        self._libraries_path = (self._vivado_path.parent.parent / "data" / "vhdl" / "src").resolve()

        self.output_path = output_path.resolve() / self._get_version_tag()

    def compile_if_needed(self) -> bool:
        """
        Compile if needed (if :meth:`compile_is_needed <.compile_is_needed>` condition is not
        fulfilled).
        """
        if self.compile_is_needed:
            self.compile()
            return True

        return False

    @property
    def compile_is_needed(self) -> bool:
        """
        If there is compiled simlib available that matches

         * Operating system
         * Vivado version
         * Simulator version

        then there should not be a recompile.

        .. note::
            Subclass implementations might add further conditions.

        Return:
            True if compiled simlib is not available. False otherwise.
        """
        if self._done_token.exists():
            return False

        return True

    def compile(self) -> None:
        """
        Compile simlib.
        """
        # Probably does not exists, but try to delete just in case.
        delete(self._done_token)

        print(f"Compiling Vivado simlib from {self._libraries_path} into {self.output_path}...")
        self._compile()

        create_file(self._done_token, "Done!")

    @abstractmethod
    def _compile(self) -> None:
        """
        Compile simlib.
        Overload in a subclass.
        """

    def add_to_vunit_project(self) -> None:
        """
        Add the compiled simlib to your VUnit project.
        """
        self._add_to_vunit_project()

    @abstractmethod
    def _add_to_vunit_project(self) -> None:
        """
        Add the compiled simlib to your VUnit project.
        Overload in a subclass.
        """

    @property
    def artifact_name(self) -> str:
        """
        The name of the folder where simlib is or will be compiled.
        Follows a format ``vivado-simlib-WW.XX.YY.ZZ`` suitable for storage and versioning
        in Artifactory.
        """
        return self.output_path.name

    def to_archive(self) -> Path:
        """
        Compress compiled simlib to an archive.

        Return:
            Path to the archive.
        """
        make_archive(str(self.output_path), "zip", self.output_path)
        archive = self.output_path.parent / (self.output_path.name + ".zip")

        return archive

    def from_archive(self, archive: Path) -> None:
        """
        Unpack compiled simlib from an existing archive.

        Arguments:
            archive: Path to a zip archive with previously compiled simlib.
        """
        with zipfile.ZipFile(archive, "r") as zip_handle:
            zip_handle.extractall(self.output_path)

    def _get_version_tag(self) -> str:
        tag = "vivado-simlib-"
        tag += self._get_operating_system_tag()
        tag += f".{self._get_vivado_version_tag()}"
        tag += f".{self._get_simulator_tag()}"
        tag += f".format_{self._format_version_id}"

        return tag

    def _get_operating_system_tag(self) -> str:
        """
        Return e.g. "linux".
        """
        return self._format_version(platform.system())

    def _get_vivado_version_tag(self) -> str:
        """
        Return e.g. "vivado_2021_2".
        """
        vivado_version = get_vivado_version(self._vivado_path)

        return self._format_version(f"vivado_{vivado_version}")

    @abstractmethod
    def _get_simulator_tag(self) -> str:
        """
        Return a simulator tag as a string, e.g. "ghdl_1.2.3".
        Overload in a subclass.
        """

    @staticmethod
    def _format_version(version: str) -> str:
        """
        Format version string to something suitable for artifactory versioning.
        """
        return version.replace(".", "_").replace("-", "_").lower()

    @property
    def _done_token(self) -> Path:
        """
        Path to "done" token file.
        """
        return self.output_path / "done.txt"
