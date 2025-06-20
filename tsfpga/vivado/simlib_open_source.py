# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, ClassVar

from tsfpga import DEFAULT_FILE_ENCODING
from tsfpga.system_utils import create_directory, system_is_windows

from .simlib_common import VivadoSimlibCommon

if TYPE_CHECKING:
    from pathlib import Path


class VivadoSimlibOpenSource(VivadoSimlibCommon):
    """
    Common methods for handling Vivado simlib with an open-source simulator.
    See subclasses for details: :class:`.VivadoSimlibGhdl`, :class:`.VivadoSimlibNvc`.

    Do not instantiate this class directly.
    Use factory class :class:`.VivadoSimlib` instead.
    """

    library_names: ClassVar = ["unisim", "secureip", "unimacro", "unifast"]

    # Set in subclass.
    _create_library_folder_before_compile: bool

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

        self._compile_library(vhd_files=vhd_files, library_name="unisim")

    def _compile_secureip(self) -> None:
        vhd_files = list((self._libraries_path / "unisims" / "secureip").glob("*.vhd"))
        self._compile_library(vhd_files=vhd_files, library_name="secureip")

    def _compile_unimacro(self) -> None:
        library_path = self._libraries_path / "unimacro"

        vhd_files = []

        vhd_file = library_path / "unimacro_VCOMP.vhd"
        if not vhd_file.exists():
            raise FileNotFoundError(f"VHDL file does not exist: {vhd_file}")
        vhd_files.append(vhd_file)

        vhd_files += self._get_compile_order(library_path=library_path)

        self._compile_library(vhd_files=vhd_files, library_name="unimacro")

    def _compile_unifast(self) -> None:
        library_path = self._libraries_path / "unifast" / "primitive"
        vhd_files = self._get_compile_order(library_path=library_path)

        self._compile_library(vhd_files=vhd_files, library_name="unifast")

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

    def _compile_library(self, vhd_files: list[Path], library_name: str) -> None:
        """
        Compile all files of the library.
        """
        output_path = self.output_path / library_name
        if self._create_library_folder_before_compile:
            create_directory(output_path, empty=True)

        # There seems to be a command length limit on Windows.
        # While compiling all files in one command gives a huge performance boost
        # (on Linux at least, as far as we know) the resulting command is in the order of
        # 90k characters long.
        # This does not seem to work on Windows.
        # So we auto detect the OS to work around this limitation, while keeping the performance
        # boost on Linux.
        compile_file_by_file = system_is_windows()

        if compile_file_by_file:
            # Compile each file in a separate command.
            for vhd_file in vhd_files:
                self._print_and_compile(
                    output_path=output_path, library_name=library_name, vhd_files=[vhd_file]
                )

        else:
            # Compile all files in one single command.
            self._print_and_compile(
                output_path=output_path, library_name=library_name, vhd_files=vhd_files
            )

    def _print_and_compile(
        self, output_path: Path, library_name: str, vhd_files: list[Path]
    ) -> None:
        """
        Print the file list and compile it.
        """
        vhd_paths_str = [str(vhd_file) for vhd_file in vhd_files]

        # Use paths relative to the Vivado installation, in order to keep it a little shorter
        # (it is still massively long).
        vhd_paths_relative = [
            str(vhd_file.relative_to(self._libraries_path)) for vhd_file in vhd_files
        ]
        paths_to_print = ", ".join(vhd_paths_relative)
        print(f"Compiling {paths_to_print} into {library_name}...")

        self._execute_compile(
            output_path=output_path, library_name=library_name, vhd_files=vhd_paths_str
        )

    @abstractmethod
    def _execute_compile(self, output_path: Path, library_name: str, vhd_files: list[str]) -> None:
        """
        Compile the files into the specified library.
        Raise exception upon failure.
        """
