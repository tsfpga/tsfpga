# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

"""
Test a subset of what is tested for commercial, since most of the code is inherited
from the common class.
"""

# Standard libraries
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third party libraries
import pytest

# First party libraries
from tsfpga.vivado.simlib import VivadoSimlib


# pylint: disable=redefined-outer-name
@pytest.fixture
def simlib_test(tmp_path):
    class SimlibGhdlTestFixture:
        def __init__(self):
            self.output_path = tmp_path / "simlib"

            self.vivado_simlib = self.get_vivado_simlib()

        def get_vivado_simlib(self, ghdl_version_string="GHDL 0.36 ..."):
            with patch("tsfpga.vivado.simlib_ghdl.subprocess.check_output") as check_output:
                check_output.return_value = ghdl_version_string.encode("UTF-8")

                simulator_class = MagicMock()
                simulator_class.name = "ghdl"
                simulator_class.find_prefix.return_value = "/usr/bin"

                vunit_proj = MagicMock()
                vunit_proj._simulator_class = simulator_class  # pylint: disable=protected-access

                vivado_simlib = VivadoSimlib.init(
                    self.output_path, vunit_proj, Path("/tools/xilinx/Vivado/2019.2/bin/vivado")
                )

                return vivado_simlib

        @staticmethod
        def assert_should_compile(vivado_simlib):
            assert vivado_simlib.compile_is_needed
            with patch(
                "tsfpga.vivado.simlib_ghdl.VivadoSimlibGhdl._compile", autospec=True
            ) as mock:
                vivado_simlib.compile_if_needed()
                mock.assert_called_once()

        @staticmethod
        def assert_should_not_compile(vivado_simlib):
            assert not vivado_simlib.compile_is_needed
            with patch(
                "tsfpga.vivado.simlib_ghdl.VivadoSimlibGhdl._compile", autospec=True
            ) as mock:
                vivado_simlib.compile_if_needed()
                mock.assert_not_called()

    return SimlibGhdlTestFixture()


def test_should_not_recompile(simlib_test):
    simlib_test.assert_should_compile(simlib_test.vivado_simlib)
    simlib_test.assert_should_not_compile(simlib_test.vivado_simlib)


def test_ghdl_version_string(simlib_test):
    assert (
        ".ghdl_0_36_v0_36."
        in simlib_test.get_vivado_simlib(
            ghdl_version_string="GHDL 0.36 (v0.36) [Dunoon edition]"
        ).artifact_name
    )
    assert (
        ".ghdl_0_36."
        in simlib_test.get_vivado_simlib(
            ghdl_version_string="GHDL 0.36 [Dunoon edition]"
        ).artifact_name
    )
    assert (
        ".ghdl_0_36_v0_36."
        in simlib_test.get_vivado_simlib(ghdl_version_string="GHDL 0.36 (v0.36)").artifact_name
    )
    assert (
        ".ghdl_0_36" in simlib_test.get_vivado_simlib(ghdl_version_string="GHDL 0.36").artifact_name
    )

    assert (
        ".ghdl_0_37_dev_v0_36_1605_ge4aa89cd"
        in simlib_test.get_vivado_simlib(
            ghdl_version_string="GHDL 0.37-dev (v0.36-1605-ge4aa89cd) [Dunoon edition]"
        ).artifact_name
    )
    assert (
        ".ghdl_0_37_dev_v0_36_1605_ge4aa89cd."
        in simlib_test.get_vivado_simlib(
            ghdl_version_string="GHDL 0.37-dev (v0.36-1605-ge4aa89cd)"
        ).artifact_name
    )
