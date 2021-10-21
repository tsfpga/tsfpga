# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import re
import subprocess
from pathlib import Path

from tsfpga import DEFAULT_FILE_ENCODING
from tsfpga.system_utils import create_directory
from .common import get_vivado_path
from .simlib_common import VivadoSimlibCommon


class VivadoSimlibGhdl(VivadoSimlibCommon):

    """
    Handle Vivado simlib with GHDL.
    """

    _libraries = ["unisim", "secureip", "unimacro", "unifast"]

    def __init__(self, output_path, vunit_proj, simulator_interface, vivado_path):
        """
        Arguments:
            output_path (pathlib.Path): The compiled simlib will be placed here.
            vunit_proj: The VUnit project that is used to run simulation.
            simulator_interface: A VUnit SimulatorInterface class.
            vivado_path (pathlib.Path): Path to Vivado executable.
        """
        self._vunit_proj = vunit_proj
        self._vivado_path = get_vivado_path(vivado_path)

        self.ghdl_binary = Path(simulator_interface.find_prefix()) / "ghdl"

        self._output_path = output_path / self._get_version_tag()

    def _compile(self):
        vivado_libraries_path = self._vivado_path.parent.parent / "data" / "vhdl" / "src"

        self._compile_unisim(vivado_libraries_path / "unisims")
        self._compile_secureip(vivado_libraries_path / "unisims" / "secureip")
        self._compile_unimacro(vivado_libraries_path / "unimacro")
        self._compile_unifast(vivado_libraries_path / "unifast" / "primitive")

    def _compile_unisim(self, library_path):
        for vhd_file_base in [
            "unisim_VPKG",
            "unisim_retarget_VCOMP",
        ]:
            vhd_file = library_path / (vhd_file_base + ".vhd")
            assert vhd_file.exists, vhd_file
            self._compile_ghdl_file(vhd_file, "unisim")

        primitive_dir = library_path / "primitive"
        for vhd_file in self._iterate_compile_order(primitive_dir):
            self._compile_ghdl_file(vhd_file, "unisim")

        retarget_dir = library_path / "retarget"
        for vhd_file in retarget_dir.glob("*.vhd"):
            self._compile_ghdl_file(vhd_file, "unisim")

    def _compile_secureip(self, library_path):
        for vhd_file in library_path.glob("*.vhd"):
            self._compile_ghdl_file(vhd_file, "secureip")

    def _compile_unimacro(self, library_path):
        vhd_file = library_path / "unimacro_VCOMP.vhd"
        assert vhd_file.exists, vhd_file
        self._compile_ghdl_file(vhd_file, "unimacro")

        for vhd_file in self._iterate_compile_order(library_path):
            self._compile_ghdl_file(vhd_file, "unimacro")

    def _compile_unifast(self, library_path):
        for vhd_file in self._iterate_compile_order(library_path):
            self._compile_ghdl_file(vhd_file, "unifast")

    @staticmethod
    def _iterate_compile_order(library_path):
        with open(
            library_path / "vhdl_analyze_order", encoding=DEFAULT_FILE_ENCODING
        ) as file_handle:
            for vhd_file_base in file_handle.readlines():
                vhd_file = library_path / vhd_file_base.strip()
                assert vhd_file.exists(), vhd_file
                yield vhd_file

    def _compile_ghdl_file(self, vhd_file, library_name):
        print(f"Compiling {vhd_file} into {library_name}")
        workdir = self._output_path / library_name / "v08"
        create_directory(workdir, empty=False)
        cmd = [
            self.ghdl_binary,
            "-a",
            "--ieee=synopsys",
            "--std=08",
            "--workdir=" + str(workdir.resolve()),
            "-P" + str(self._output_path),
            "-fexplicit",
            "-frelaxed-rules",
            "--no-vital-checks",
            "--warn-binding",
            "--mb-comments",
            "--work=" + library_name,
            str(vhd_file.resolve()),
        ]
        subprocess.check_call(cmd, cwd=self._output_path)

    def _get_simulator_tag(self):
        """
        Return simulator version tag
        """
        cmd = [self.ghdl_binary, "--version"]
        output = subprocess.check_output(cmd).decode()

        regexp_with_tag = re.compile(r"^GHDL (\S+) \((\S+)\).*")
        match = regexp_with_tag.search(output)
        if match is not None:
            return self._format_version(f"ghdl_{match.group(1)}_{match.group(2)}")

        regexp_without_tag = re.compile(r"^GHDL (\S+).*")
        match = regexp_without_tag.search(output)
        if match is not None:
            return self._format_version("ghdl_" + match.group(1))

        raise ValueError("Could not find GHDL version string: " + output)

    def _add_to_vunit_project(self):
        """
        Add the compiled simlib to your VUnit project.
        """
        for library in self._libraries:
            library_path = self._output_path / library / "v08"
            assert library_path.exists(), library_path
            self._vunit_proj.add_external_library(library, library_path)
