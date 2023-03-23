# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import re
import subprocess
from pathlib import Path

# First party libraries
from tsfpga import DEFAULT_FILE_ENCODING
from tsfpga.system_utils import create_directory

# Local folder libraries
from .simlib_common import VivadoSimlibCommon


class VivadoSimlibGhdl(VivadoSimlibCommon):

    """
    Handle Vivado simlib with GHDL.
    """

    library_names = ["unisim", "secureip", "unimacro", "unifast"]

    def __init__(self, output_path, vunit_proj, simulator_interface, vivado_path):
        """
        Arguments:
            output_path (pathlib.Path): The compiled simlib will be placed here.
            vunit_proj: The VUnit project that is used to run simulation.
            simulator_interface: A VUnit SimulatorInterface class.
            vivado_path (pathlib.Path): Path to Vivado executable.
        """
        self.ghdl_binary = Path(simulator_interface.find_prefix()) / "ghdl"

        super().__init__(vivado_path=vivado_path, output_path=output_path)

        self._vunit_proj = vunit_proj

    def _compile(self):
        self._compile_unisim()
        self._compile_secureip()
        self._compile_unimacro()
        self._compile_unifast()

    def _compile_unisim(self):
        library_path = self._libraries_path / "unisims"

        vhd_files = []

        for vhd_file_base in [
            "unisim_VPKG",
            "unisim_retarget_VCOMP",
        ]:
            vhd_file = library_path / f"{vhd_file_base}.vhd"
            assert vhd_file.exists, vhd_file
            vhd_files.append(vhd_file)

        primitive_dir = library_path / "primitive"
        vhd_files += self._get_compile_order(library_path=primitive_dir)

        retarget_dir = library_path / "retarget"
        for vhd_file in retarget_dir.glob("*.vhd"):
            vhd_files.append(vhd_file)

        self._compile_ghdl(vhd_files=vhd_files, library_name="unisim")

    def _compile_secureip(self):
        library_path = self._libraries_path / "unisims" / "secureip"

        vhd_files = []
        for vhd_file in library_path.glob("*.vhd"):
            vhd_files.append(vhd_file)

        self._compile_ghdl(vhd_files=vhd_files, library_name="secureip")

    def _compile_unimacro(self):
        library_path = self._libraries_path / "unimacro"

        vhd_files = []

        vhd_file = library_path / "unimacro_VCOMP.vhd"
        assert vhd_file.exists, vhd_file
        vhd_files.append(vhd_file)

        vhd_files += self._get_compile_order(library_path=library_path)

        self._compile_ghdl(vhd_files=vhd_files, library_name="unimacro")

    def _compile_unifast(self):
        library_path = self._libraries_path / "unifast" / "primitive"
        vhd_files = self._get_compile_order(library_path=library_path)

        self._compile_ghdl(vhd_files=vhd_files, library_name="unifast")

    @staticmethod
    def _get_compile_order(library_path):
        """
        Get compile order (list of file paths, in order) from an existing compile order
        file provided by Xilinx.
        """
        vhd_files = []

        with open(
            library_path / "vhdl_analyze_order", encoding=DEFAULT_FILE_ENCODING
        ) as file_handle:
            for vhd_file_base in file_handle.readlines():
                vhd_file = library_path / vhd_file_base.strip()
                assert vhd_file.exists(), vhd_file
                vhd_files.append(vhd_file)

        return vhd_files

    def _compile_ghdl(self, vhd_files, library_name):
        """
        Compile a list of files into the specified library.
        """
        # Print a list of the files that will be compiled.
        # Relative paths to the Vivado path, which we printed earlier, in order to keep it a little
        # shorter (it is still massively long).
        relative_paths = [vhd_file.relative_to(self._libraries_path) for vhd_file in vhd_files]
        paths_to_print = ", ".join([str(path) for path in relative_paths])
        print(f"Compiling {paths_to_print} into {library_name}...")

        workdir = self.output_path / library_name
        create_directory(workdir, empty=False)

        cmd = [
            self.ghdl_binary,
            "-a",
            "--ieee=synopsys",
            "--std=08",
            f"--workdir={str(workdir.resolve())}",
            f"-P{str(self.output_path / 'unisim')}",
            "-fexplicit",
            "-frelaxed-rules",
            "--no-vital-checks",
            "--warn-binding",
            "--mb-comments",
            f"--work={library_name}",
        ]
        cmd += [str(vhd_file) for vhd_file in vhd_files]

        subprocess.check_call(cmd, cwd=self.output_path)

    def _get_simulator_tag(self):
        """
        Return simulator version tag as a string.
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
            return self._format_version(f"ghdl_{match.group(1)}")

        raise ValueError(f"Could not find GHDL version string: {output}")

    def _add_to_vunit_project(self):
        """
        Add the compiled simlib to your VUnit project.
        """
        for library_name in self.library_names:
            library_path = self.output_path / library_name
            assert library_path.exists(), library_path
            self._vunit_proj.add_external_library(library_name, library_path)
