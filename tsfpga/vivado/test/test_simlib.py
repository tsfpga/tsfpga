# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest

from tsfpga.vivado.simlib import VivadoSimlib

# pylint: disable=unused-import
from tsfpga.test.conftest import fixture_tmp_path  # noqa: F401


@pytest.mark.usefixtures("fixture_tmp_path")
class TestVivadoSimlibCommercial(TestCase):

    tmp_path = None

    def setUp(self):
        self.output_path = self.tmp_path / "simlib"

        self.simulator_prefix = "/opt/Aldec/Riviera-PRO-2018.10-x64/bin"
        self.vivado_path = Path("/tools/xilinx/Vivado/2019.2/bin/vivado")

        self.vivado_simlib = self.get_vivado_simlib(self.simulator_prefix, self.vivado_path)

    def get_vivado_simlib(self, simulator_prefix, vivado_path):
        simulator_class = MagicMock()
        simulator_class.name = "rivierapro"
        simulator_class.find_prefix.return_value = simulator_prefix

        vunit_proj = MagicMock()
        vunit_proj._simulator_class = simulator_class  # pylint: disable=protected-access

        return VivadoSimlib.init(self.output_path, vunit_proj, vivado_path)

    def test_should_not_recompile(self):
        self.assert_should_compile(self.vivado_simlib)
        self.assert_should_not_compile(self.vivado_simlib)

    def test_new_simulator_version_should_cause_recompile(self):
        self.assert_should_compile(self.vivado_simlib)
        self.assert_should_not_compile(self.vivado_simlib)

        vivado_simlib = self.get_vivado_simlib(
            "/opt/Aldec/Riviera-PRO-1975.01-x64/bin", self.vivado_path
        )
        self.assert_should_compile(vivado_simlib)
        self.assert_should_not_compile(vivado_simlib)

    def test_new_vivado_version_should_cause_recompile(self):
        self.assert_should_compile(self.vivado_simlib)
        self.assert_should_not_compile(self.vivado_simlib)

        vivado_simlib = self.get_vivado_simlib(
            self.simulator_prefix, Path("/tools/xilinx/Vivado/1337.2/bin/vivado")
        )
        self.assert_should_compile(vivado_simlib)
        self.assert_should_not_compile(vivado_simlib)

    @staticmethod
    def assert_should_compile(vivado_simlib):
        assert vivado_simlib.compile_is_needed
        with patch("tsfpga.vivado.simlib_commercial.run_vivado_tcl", autospec=True) as mock:
            vivado_simlib.compile_if_needed()
            mock.assert_called_once()

    @staticmethod
    def assert_should_not_compile(vivado_simlib):
        assert not vivado_simlib.compile_is_needed
        with patch("tsfpga.vivado.simlib_commercial.run_vivado_tcl", autospec=True) as mock:
            vivado_simlib.compile_if_needed()
            mock.assert_not_called()


@pytest.mark.usefixtures("fixture_tmp_path")
class TestVivadoSimlibGhdl(TestCase):

    """
    Test a subset of what is tested for commercial, since most of the code is inherited
    from the common class.
    """

    tmp_path = None

    def setUp(self):
        self.output_path = self.tmp_path / "simlib"

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

    def test_should_not_recompile(self):
        self.assert_should_compile(self.vivado_simlib)
        self.assert_should_not_compile(self.vivado_simlib)

    def test_ghdl_version_string(self):
        assert self.get_vivado_simlib(
            ghdl_version_string="GHDL 0.36 (v0.36) [Dunoon edition]"
        ).artifact_name.endswith(".ghdl_0_36_v0_36")
        assert self.get_vivado_simlib(
            ghdl_version_string="GHDL 0.36 [Dunoon edition]"
        ).artifact_name.endswith(".ghdl_0_36")
        assert self.get_vivado_simlib(
            ghdl_version_string="GHDL 0.36 (v0.36)"
        ).artifact_name.endswith(".ghdl_0_36_v0_36")
        assert self.get_vivado_simlib(ghdl_version_string="GHDL 0.36").artifact_name.endswith(
            ".ghdl_0_36"
        )

        assert self.get_vivado_simlib(
            ghdl_version_string="GHDL 0.37-dev (v0.36-1605-ge4aa89cd) [Dunoon edition]"
        ).artifact_name.endswith(".ghdl_0_37_dev_v0_36_1605_ge4aa89cd")
        assert self.get_vivado_simlib(
            ghdl_version_string="GHDL 0.37-dev (v0.36-1605-ge4aa89cd)"
        ).artifact_name.endswith(".ghdl_0_37_dev_v0_36_1605_ge4aa89cd")

    @staticmethod
    def assert_should_compile(vivado_simlib):
        assert vivado_simlib.compile_is_needed
        with patch("tsfpga.vivado.simlib_ghdl.VivadoSimlibGhdl._compile", autospec=True) as mock:
            vivado_simlib.compile_if_needed()
            mock.assert_called_once()

    @staticmethod
    def assert_should_not_compile(vivado_simlib):
        assert not vivado_simlib.compile_is_needed
        with patch("tsfpga.vivado.simlib_ghdl.VivadoSimlibGhdl._compile", autospec=True) as mock:
            vivado_simlib.compile_if_needed()
            mock.assert_not_called()
