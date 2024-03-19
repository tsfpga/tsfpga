# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path

# Third party libraries
import pytest

# First party libraries
from tsfpga.hdl_file import HdlFile


def test_file_endings():
    assert HdlFile.file_endings == (".vhd", ".vhdl", ".v", ".vh", ".sv", ".svh")


def test_file_type():
    assert HdlFile(Path("file.vhd")).type == HdlFile.Type.VHDL
    assert HdlFile(Path("file.vhdl")).type == HdlFile.Type.VHDL

    assert HdlFile(Path("file.v")).type == HdlFile.Type.VERILOG_SOURCE
    assert HdlFile(Path("file.vh")).type == HdlFile.Type.VERILOG_HEADER

    assert HdlFile(Path("file.sv")).type == HdlFile.Type.SYSTEMVERILOG_SOURCE
    assert HdlFile(Path("file.svh")).type == HdlFile.Type.SYSTEMVERILOG_HEADER


def test_unknown_file_ending_raises_exception():
    with pytest.raises(ValueError) as exception_info:
        HdlFile(Path("file.unknown"))
    assert str(exception_info.value) == "Unsupported HDL file ending: file.unknown"


def test_can_cast_to_string_without_error():
    str(HdlFile(Path("file.vhd")))
