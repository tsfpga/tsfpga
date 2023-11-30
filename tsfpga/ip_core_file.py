# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path
from typing import Any


class IpCoreFile:
    """
    Class for handling an IP core file.
    """

    def __init__(self, path: Path, **variables: Any) -> None:
        """
        Arguments:
            path: Path to the TCL script that creates the IP.
                Should typically end in .tcl.
            variables: These name/value variable pairs will be set in TCL before
                the IP core ``.tcl`` file is sourced. This makes it possible to parameterize the IP
                core creation.

                .. note::
                    This is a "kwargs" style argument. You can pass any number of named arguments.
        """
        self.path = path
        self.variables = variables

    @property
    def name(self) -> str:
        """
        A shorthand name for this IP core.
        """
        file_name_no_suffix = self.path.stem
        if " " in file_name_no_suffix:
            raise ValueError(f"File name may not contain spaces: {self.path}")
        return file_name_no_suffix

    def __str__(self) -> str:
        return f"{self.__class__.__name__}:{self.path}:{self.variables}"
