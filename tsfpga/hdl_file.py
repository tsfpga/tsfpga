# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path


class HdlFile:
    """
    Class for representing a HDL source code file.
    """

    vhdl_file_ending = (".vhd", ".vhdl")
    verilog_source_file_ending = (".v",)
    verilog_header_file_ending = (".vh",)
    system_verilog_source_file_ending = (".sv",)
    system_verilog_header_file_ending = (".svh",)

    file_endings = (
        *vhdl_file_ending,
        *verilog_source_file_ending,
        *verilog_header_file_ending,
        *system_verilog_source_file_ending,
        *system_verilog_header_file_ending,
    )

    def __init__(self, path: Path) -> None:
        """
        Arguments:
            path: Path to a HDL source code  file.
        """
        self.path = path

    @property
    def is_vhdl(self) -> bool:
        """
        True if the file is a VHDL file. Otherwise False.
        """
        return self._is_file_ending(file_endings=self.vhdl_file_ending)

    @property
    def is_verilog_source(self) -> bool:
        """
        True if the file is a Verilog source file. Otherwise False.
        """
        return self._is_file_ending(file_endings=self.verilog_source_file_ending)

    @property
    def is_verilog_header(self) -> bool:
        """
        True if the file is a Verilog header file. Otherwise False.
        """
        return self._is_file_ending(file_endings=self.verilog_header_file_ending)

    @property
    def is_verilog(self) -> bool:
        """
        True if the file is a Verilog file (header or source). Otherwise False.
        """
        return self.is_verilog_source or self.is_verilog_header

    @property
    def is_systemverilog_source(self) -> bool:
        """
        True if the file is a SystemVerilog source file. Otherwise False.
        """
        return self._is_file_ending(file_endings=self.system_verilog_source_file_ending)

    @property
    def is_systemverilog_header(self) -> bool:
        """
        True if the file is a SystemVerilog header file. Otherwise False.
        """
        return self._is_file_ending(file_endings=self.system_verilog_header_file_ending)

    @property
    def is_systemverilog(self) -> bool:
        """
        True if the file is a SystemVerilog file (header or source). Otherwise False.
        """
        return self.is_systemverilog_source or self.is_systemverilog_header

    def _is_file_ending(self, file_endings: tuple[str, ...]) -> bool:
        return self.path.name.endswith(file_endings)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}('{self.path}')"
