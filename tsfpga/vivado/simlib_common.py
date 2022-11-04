# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import platform
import zipfile
from shutil import make_archive

# First party libraries
from tsfpga.system_utils import create_file, delete
from tsfpga.vivado.common import get_vivado_version


class VivadoSimlibCommon:

    """
    Class for handling Vivado simlib used for simulation. Keeps track of when a
    (re)compile is needed.

    This is a parent class that defines an interface and some common methods.
    See child classes for details: :class:`.VivadoSimlibGhdl`, :class:`.VivadoSimlibCommercial`.
    """

    # The version of this class. Can be bumped to force a re-compile if e.g. the TCL script changes
    # or the output folder structure is updated.
    _format_version_id = 2

    # Set in child class to a list of strings. The libraries that shall be compiled and added to
    # VUnit project.
    library_names = None

    # Set in child class to a pathlib.Path object. The path to the "vivado" executable.
    _vivado_path = None

    # Set in child class to a pathlib.Path object. The path where simlib shall be compiled.
    output_path = None

    def compile_if_needed(self):
        """
        Compile if needed (if :meth:`compile_is_needed <.compile_is_needed>` condition is not
        fulfilled).
        """
        if self.compile_is_needed:
            self.compile()
            return True
        return False

    @property
    def compile_is_needed(self):
        """
        If there is compiled simlib available that matches

         * Operating system
         * Vivado version
         * Simulator version

        then there should not be a recompile.

        .. note::
            Child implementations might add further conditions.

        Return:
            True if compiled simlib is not available. False otherwise.
        """
        if self._done_token.exists():
            return False
        return True

    def compile(self):
        """
        Compile simlib.
        """
        delete(self._done_token)
        print(f"Compiling Vivado simlib in {self.output_path}")

        self._compile()

        create_file(self._done_token, "Done!")

    def _compile(self):
        """
        Compile simlib.
        """
        raise NotImplementedError()

    def add_to_vunit_project(self):
        """
        Add the compiled simlib to your VUnit project.
        """
        self._add_to_vunit_project()

    def _add_to_vunit_project(self):
        raise NotImplementedError()

    @property
    def artifact_name(self):
        """
        str: The name of the folder where simlib is or will be compiled.
        Follows a format ``vivado-simlib-WW.XX.YY.ZZ`` suitable for storage and versioning
        in Artifactory.
        """
        return self.output_path.name

    def to_archive(self):
        """
        Compress compiled simlib to an archive.

        Return:
            pathlib.Path: Path to the archive.
        """
        make_archive(self.output_path, "zip", self.output_path)
        archive = self.output_path.parent / (self.output_path.name + ".zip")
        return archive

    def from_archive(self, archive):
        """
        Unpack compiled simlib from an existing archive.

        Arguments:
            archive (pathlib.Path): Path to a zip archive with previously compiled simlib.
        """
        with zipfile.ZipFile(archive, "r") as zip_handle:
            zip_handle.extractall(self.output_path)

    def _get_version_tag(self):
        tag = "vivado-simlib-"
        tag += self._get_operating_system_tag()
        tag += f".{self._get_vivado_version_tag()}"
        tag += f".{self._get_simulator_tag()}"
        tag += f".format_{self._format_version_id}"

        return tag

    def _get_operating_system_tag(self):
        """
        Return e.g. "linux".
        """
        return self._format_version(platform.system())

    def _get_vivado_version_tag(self):
        """
        Return e.g. "vivado_2021_2".
        """
        vivado_version = get_vivado_version(self._vivado_path)

        return self._format_version(f"vivado_{vivado_version}")

    def _get_simulator_tag(self):
        raise NotImplementedError()

    @staticmethod
    def _format_version(version):
        """
        Format version string to something suitable for artifactory versioning.
        """
        return version.replace(".", "_").replace("-", "_").lower()

    @property
    def _done_token(self):
        """
        Path to "done" token file.
        """
        return self.output_path / "done.txt"
