# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import dirname, join
from unittest import TestCase
from unittest.mock import MagicMock, patch

from tsfpga.system_utils import delete
from tsfpga.vivado_simlib import VivadoSimlib


THIS_DIR = dirname(__file__)


class TestVivadoSimlib(TestCase):

    def setUp(self):
        self.output_path = join(THIS_DIR, "simlib")
        delete(self.output_path)

        self.vunit_mock = MagicMock()
        #  pylint: disable=protected-access
        self.vunit_mock.get_simulator_name.return_value = "rivierapro"
        self.vunit_mock._simulator_class.find_prefix.return_value = \
            "/opt/Aldec/Riviera-PRO-2018.10-x64/bin"

        self.vivado_path = "/tools/xilinx/Vivado/2019.1/bin/vivado"

    def test_should_not_recompile(self):
        vivado_simlib = VivadoSimlib(self.vunit_mock, self.output_path, self.vivado_path)
        self.assert_should_compile(vivado_simlib)
        self.assert_should_not_compile(vivado_simlib)

    def test_new_simulator_version_should_cause_recompile(self):
        vivado_simlib = VivadoSimlib(self.vunit_mock, self.output_path, self.vivado_path)
        self.assert_should_compile(vivado_simlib)
        vivado_simlib = VivadoSimlib(self.vunit_mock, self.output_path, self.vivado_path)
        self.assert_should_not_compile(vivado_simlib)

        #  pylint: disable=protected-access
        self.vunit_mock._simulator_class.find_prefix.return_value = \
            "/opt/Aldec/Riviera-PRO-2017.10-x64/bin"
        vivado_simlib = VivadoSimlib(self.vunit_mock, self.output_path, self.vivado_path)
        self.assert_should_compile(vivado_simlib)
        self.assert_should_not_compile(vivado_simlib)

    def test_new_vivado_version_should_cause_recompile(self):
        vivado_simlib = VivadoSimlib(self.vunit_mock, self.output_path, self.vivado_path)
        self.assert_should_compile(vivado_simlib)
        vivado_simlib = VivadoSimlib(self.vunit_mock, self.output_path, self.vivado_path)
        self.assert_should_not_compile(vivado_simlib)

        vivado_path = "/opt/xilinx/Vivado/2018.0/bin/vivado"
        vivado_simlib = VivadoSimlib(self.vunit_mock, self.output_path, vivado_path)
        self.assert_should_compile(vivado_simlib)
        self.assert_should_not_compile(vivado_simlib)

    @staticmethod
    def assert_should_compile(vivado_simlib):
        with patch("tsfpga.vivado_simlib.run_vivado_tcl", autospec=True) as mock:
            vivado_simlib.compile_if_needed()
            mock.assert_called_once()

    @staticmethod
    def assert_should_not_compile(vivado_simlib):
        with patch("tsfpga.vivado_simlib.run_vivado_tcl", autospec=True) as mock:
            vivado_simlib.compile_if_needed()
            mock.assert_not_called()
