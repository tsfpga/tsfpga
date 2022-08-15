# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tsfpga.vivado.simlib import VivadoSimlib
from tsfpga.test.test_utils import file_contains_string


# pylint: disable=redefined-outer-name
@pytest.fixture
def simlib_commercial_test():
    class SimlibCommercialTestFixture:
        def __init__(self, tmp_path):
            self.output_path = tmp_path / "simlib"

            self.simulator_prefix = "/opt/Aldec/Riviera-PRO-2018.10-x64/bin"
            self.vivado_path = Path("/tools/xilinx/Vivado/2019.2/bin/vivado")

            self.vivado_simlib = self.get_vivado_simlib(self.simulator_prefix, self.vivado_path)

        def get_vivado_simlib(
            self, simulator_prefix, vivado_path, simulator_class_name="rivierapro"
        ):
            simulator_class = MagicMock()
            simulator_class.name = simulator_class_name
            simulator_class.find_prefix.return_value = simulator_prefix

            vunit_proj = MagicMock()
            vunit_proj._simulator_class = simulator_class  # pylint: disable=protected-access

            return VivadoSimlib.init(self.output_path, vunit_proj, vivado_path)

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

    return SimlibCommercialTestFixture


def test_should_not_recompile(simlib_commercial_test, tmp_path):
    test = simlib_commercial_test(tmp_path=tmp_path)

    test.assert_should_compile(test.vivado_simlib)
    test.assert_should_not_compile(test.vivado_simlib)


def test_new_simulator_version_should_cause_recompile(simlib_commercial_test, tmp_path):
    test = simlib_commercial_test(tmp_path=tmp_path)

    test.assert_should_compile(test.vivado_simlib)
    test.assert_should_not_compile(test.vivado_simlib)

    vivado_simlib = test.get_vivado_simlib(
        simulator_prefix="/opt/Aldec/Riviera-PRO-1975.01-x64/bin", vivado_path=test.vivado_path
    )
    test.assert_should_compile(vivado_simlib)
    test.assert_should_not_compile(vivado_simlib)


def test_new_vivado_version_should_cause_recompile(simlib_commercial_test, tmp_path):
    test = simlib_commercial_test(tmp_path=tmp_path)

    test.assert_should_compile(test.vivado_simlib)
    test.assert_should_not_compile(test.vivado_simlib)

    vivado_simlib = test.get_vivado_simlib(
        simulator_prefix=test.simulator_prefix,
        vivado_path=Path("/tools/xilinx/Vivado/1337.2/bin/vivado"),
    )
    test.assert_should_compile(vivado_simlib)
    test.assert_should_not_compile(vivado_simlib)


def test_remapping_of_vivado_simulator_names(simlib_commercial_test, tmp_path):
    test = simlib_commercial_test(tmp_path=tmp_path)

    def check_simulator_name(vivado_simlib, name):
        with patch("tsfpga.vivado.simlib_commercial.run_vivado_tcl", autospec=True) as _:
            vivado_simlib.compile_if_needed()

        assert file_contains_string(
            file=vivado_simlib.output_path / "compile_simlib.tcl",
            string=f"compile_simlib -simulator {name} -simulator_exec_path ",
        )

    # Regular Siemens ModelSim should be called "modelsim"
    vivado_simlib = test.get_vivado_simlib(
        simulator_prefix=Path("/opt/intelFPGA/20.1/modelsim_ase/bin/"),
        vivado_path=Path("/tools/xilinx/Vivado/2019.2/bin/vivado"),
        simulator_class_name="modelsim",
    )
    check_simulator_name(vivado_simlib=vivado_simlib, name="modelsim")

    # Siemens Questa is called "modelsim" in VUnit but Vivado needs the name "questasim".
    vivado_simlib = test.get_vivado_simlib(
        simulator_prefix=Path("/opt/intelFPGA_pro/22.2/questa_fse/bin"),
        vivado_path=Path("/tools/xilinx/Vivado/2019.2/bin/vivado"),
        simulator_class_name="modelsim",
    )
    check_simulator_name(vivado_simlib=vivado_simlib, name="questasim")

    # Aldec Riviera-PRO is called "rivierapro" in VUnit but Vivado needs the name "riviera"
    vivado_simlib = test.get_vivado_simlib(
        simulator_prefix=Path("/opt/Aldec/Riviera-PRO-1975.01-x64/bin"),
        vivado_path=Path("/tools/xilinx/Vivado/2019.2/bin/vivado"),
        simulator_class_name="rivierapro",
    )
    check_simulator_name(vivado_simlib=vivado_simlib, name="riviera")
