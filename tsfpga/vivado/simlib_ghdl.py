# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from tsfpga import DEFAULT_FILE_ENCODING
from tsfpga.system_utils import create_directory, run_command, system_is_windows

from .simlib_common import VivadoSimlibCommon

if TYPE_CHECKING:
    from vunit.sim_if import SimulatorInterface
    from vunit.ui import VUnit


class VivadoSimlibGhdl(VivadoSimlibCommon):
    """
    Handle Vivado simlib with GHDL.
    """

    library_names: ClassVar = ["unisim", "secureip", "unimacro", "unifast"]

    def __init__(
        self,
        vivado_path: Path | None,
        output_path: Path,
        vunit_proj: VUnit,
        simulator_interface: SimulatorInterface,
    ) -> None:
        """
        Arguments:
            output_path: The compiled simlib will be placed here.
            vunit_proj: The VUnit project that is used to run simulation.
            simulator_interface: A VUnit SimulatorInterface class.
            vivado_path: Path to Vivado executable.
        """
        self.ghdl_binary = Path(simulator_interface.find_prefix()) / "ghdl"

        super().__init__(vivado_path=vivado_path, output_path=output_path)

        self._vunit_proj = vunit_proj

    def _compile(self) -> None:
        self._compile_unisim()
        self._compile_secureip()
        self._compile_unimacro()
        self._compile_unifast()

    def _compile_unisim(self) -> None:
        library_path = self._libraries_path / "unisims"

        vhd_files = []

        for vhd_file_base in [
            "unisim_VPKG",
            "unisim_retarget_VCOMP",
        ]:
            vhd_file = library_path / f"{vhd_file_base}.vhd"
            if not vhd_file.exists():
                raise FileNotFoundError(f"VHDL file does not exist: {vhd_file}")

            vhd_files.append(vhd_file)

        primitive_dir = library_path / "primitive"
        vhd_files += self._get_compile_order(library_path=primitive_dir)

        retarget_dir = library_path / "retarget"
        for vhd_file in retarget_dir.glob("*.vhd"):
            vhd_files.append(vhd_file)

        self._compile_ghdl(vhd_files=vhd_files, library_name="unisim")

    def _compile_secureip(self) -> None:
        vhd_files = (self._libraries_path / "unisims" / "secureip").glob("*.vhd")
        self._compile_ghdl(vhd_files=vhd_files, library_name="secureip")

    def _compile_unimacro(self) -> None:
        library_path = self._libraries_path / "unimacro"

        vhd_files = []

        vhd_file = library_path / "unimacro_VCOMP.vhd"
        if not vhd_file.exists():
            raise FileNotFoundError(f"VHDL file does not exist: {vhd_file}")
        vhd_files.append(vhd_file)

        vhd_files += self._get_compile_order(library_path=library_path)

        self._compile_ghdl(vhd_files=vhd_files, library_name="unimacro")

    def _compile_unifast(self) -> None:
        library_path = self._libraries_path / "unifast" / "primitive"
        vhd_files = self._get_compile_order(library_path=library_path)

        self._compile_ghdl(vhd_files=vhd_files, library_name="unifast")

    @staticmethod
    def _get_compile_order(library_path: Path) -> list[Path]:
        """
        Get compile order (list of file paths, in order) from an existing compile order
        file provided by Xilinx.
        """
        vhd_files = []

        with (library_path / "vhdl_analyze_order").open(
            encoding=DEFAULT_FILE_ENCODING
        ) as file_handle:
            for vhd_file_base in file_handle:
                vhd_file = library_path / vhd_file_base.strip()
                if not vhd_file.exists():
                    raise FileNotFoundError(f"VHDL file does not exist: {vhd_file}")

                vhd_files.append(vhd_file)

        return vhd_files

    def _compile_ghdl(self, vhd_files: list[Path], library_name: str) -> None:
        """
        Compile a list of files into the specified library.
        """
        workdir = self.output_path / library_name
        create_directory(workdir, empty=False)

        vhd_paths_str = [str(vhd_file) for vhd_file in vhd_files]
        # We print a list of the files that will be compiled.
        # Use relative paths to the Vivado path, in order to keep it a little shorter
        # (it is still massively long).
        vhd_paths_relative = [
            str(vhd_file.relative_to(self._libraries_path)) for vhd_file in vhd_files
        ]

        def print_compiling(path: str) -> None:
            print(f"Compiling {path} into {library_name}...")

        def execute_ghdl(files: list[str]) -> None:
            self._execute_ghdl(workdir=workdir, library_name=library_name, files=files)

        # There seems to be a command length limit on Windows.
        # While compiling all files in one command gives a huge performance boost
        # (on Linux with GCC backend at least, as far as we know) the resulting command is in
        # the order of 90k characters long.
        # This does not seem to work on Windows.
        # So we auto detect the OS to work around this limitation, while keeping the performance
        # boost on Linux.
        compile_file_by_file = system_is_windows()

        if compile_file_by_file:
            # Compile each file in a separate command.
            for vhd_file_idx, vhd_file_str in enumerate(vhd_paths_str):
                print_compiling(vhd_paths_relative[vhd_file_idx])
                execute_ghdl(files=[vhd_file_str])

        else:
            # Compile all files in one single command.
            paths_to_print = ", ".join(vhd_paths_relative)
            print_compiling(paths_to_print)
            execute_ghdl(files=vhd_paths_str)

    def _execute_ghdl(self, workdir: Path, library_name: str, files: list[str]) -> None:
        cmd = [
            str(self.ghdl_binary),
            "-a",
            "--ieee=synopsys",
            "--std=08",
            f"--workdir={workdir.resolve()}",
            f"-P{self.output_path / 'unisim'}",
            "-fexplicit",
            "-frelaxed-rules",
            "--no-vital-checks",
            "--warn-binding",
            "--mb-comments",
            f"--work={library_name}",
            *files,
        ]

        run_command(cmd, cwd=self.output_path)

    def _get_simulator_tag(self) -> str:
        """
        Return simulator version tag as a string.
        """
        cmd = [str(self.ghdl_binary), "--version"]
        output = run_command(cmd, capture_output=True).stdout

        regexp_with_tag = re.compile(r"^GHDL (\S+) \((\S+)\).*")
        match = regexp_with_tag.search(output)
        if match is not None:
            return self._format_version(f"ghdl_{match.group(1)}_{match.group(2)}")

        regexp_without_tag = re.compile(r"^GHDL (\S+).*")
        match = regexp_without_tag.search(output)
        if match is not None:
            return self._format_version(f"ghdl_{match.group(1)}")

        raise ValueError(f"Could not find GHDL version string: {output}")

    def _add_to_vunit_project(self) -> None:
        """
        Add the compiled simlib to your VUnit project.
        """
        for library_name in self.library_names:
            library_path = self.output_path / library_name
            if not library_path.exists():
                raise FileNotFoundError(f"Library path does not exist: {library_path}")

            self._vunit_proj.add_external_library(library_name, library_path)
