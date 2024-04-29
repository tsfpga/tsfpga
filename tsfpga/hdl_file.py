# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from enum import Enum, auto
from pathlib import Path


class HdlFile:
    """
    Class for representing a HDL source code file in the file system.
    """

    class Type(Enum):
        """
        Enumeration of supported HDL file types.
        """

        VHDL = auto()
        VERILOG_SOURCE = auto()
        VERILOG_HEADER = auto()
        SYSTEMVERILOG_SOURCE = auto()
        SYSTEMVERILOG_HEADER = auto()

    # Decides which file endings are associated with which file type.
    file_endings_mapping = {
        Type.VHDL: (".vhd", ".vhdl"),
        Type.VERILOG_SOURCE: (".v",),
        Type.VERILOG_HEADER: (".vh",),
        Type.SYSTEMVERILOG_SOURCE: (".sv",),
        Type.SYSTEMVERILOG_HEADER: (".svh",),
    }

    # A tuple of all supported HDL file endings.
    file_endings = tuple(
        file_ending
        for type_file_endings in file_endings_mapping.values()
        for file_ending in type_file_endings
    )

    def __init__(self, path: Path) -> None:
        """
        Arguments:
            path: Path to a HDL source code  file.
        """
        self._path = path

        for file_type, file_endings in self.file_endings_mapping.items():
            if path.name.endswith(file_endings):
                self._type = file_type
                break
        else:
            raise ValueError(f"Unsupported HDL file ending: {path}")

    @property
    def path(self) -> Path:
        """
        Path to the HDL file.
        Getter for read-only class variable.
        """
        return self._path

    @property
    def type(self) -> Type:
        """
        The file type of the HDL file.
        Getter for read-only class variable.
        """
        return self._type

    def __str__(self) -> str:
        return f"{self.__class__.__name__}('{self._path}', '{self._type}')"

    def __repr__(self) -> str:
        return str(self)
