# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path

# Third party libraries
import pytest

# First party libraries
from tsfpga.ip_core_file import IpCoreFile


def test_can_cast_to_string_without_error():
    str(IpCoreFile(Path("/apa/my_core.tcl")))
    str(IpCoreFile(Path("/apa/my_core.tcl"), apa=123, hest="true", zebra=False))


def test_name():
    assert IpCoreFile(Path("/apa/my_core.tcl")).name == "my_core"


def test_name_with_spaces_should_raise_exception():
    with pytest.raises(ValueError) as exception_info:
        # pylint: disable=expression-not-assigned
        IpCoreFile(Path("/apa/my core.tcl")).name
    assert str(exception_info.value) == "File name may not contain spaces: /apa/my core.tcl"
