# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

"""
Test a subset of what is tested for commercial, since most of the code is inherited
from the common class.
"""

# Standard libraries
from pathlib import Path
from unittest.mock import MagicMock, call, patch

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
            with patch("tsfpga.vivado.simlib_ghdl.run_command", autospec=True) as run_command:
                run_command.return_value.stdout = ghdl_version_string

                simulator_class = MagicMock()
                simulator_class.name = "ghdl"
                simulator_class.find_prefix.return_value = "/usr/bin"

                vunit_proj = MagicMock()
                vunit_proj._simulator_class = simulator_class  # pylint: disable=protected-access

                vivado_simlib = VivadoSimlib.init(
                    self.output_path, vunit_proj, Path("/tools/xilinx/Vivado/2019.2/bin/vivado")
                )

                return vivado_simlib

        def assert_should_compile(self):
            assert self.vivado_simlib.compile_is_needed
            with patch(
                "tsfpga.vivado.simlib_ghdl.VivadoSimlibGhdl._compile", autospec=True
            ) as mock:
                self.vivado_simlib.compile_if_needed()
                mock.assert_called_once()

        def assert_should_not_compile(self):
            assert not self.vivado_simlib.compile_is_needed
            with patch(
                "tsfpga.vivado.simlib_ghdl.VivadoSimlibGhdl._compile", autospec=True
            ) as mock:
                self.vivado_simlib.compile_if_needed()
                mock.assert_not_called()

    return SimlibGhdlTestFixture()


def test_should_not_recompile(simlib_test):
    simlib_test.assert_should_compile()
    simlib_test.assert_should_not_compile()


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


def test_should_compile_file_by_file_on_windows_but_not_on_linux(simlib_test):
    library_name = "unisim"

    # pylint: disable=protected-access
    unisim_path = simlib_test.vivado_simlib._libraries_path / library_name
    vhd_files = [unisim_path / "a.vhd", unisim_path / "b.vhd"]

    def run_test(is_windows, expected_calls):
        with patch.object(
            simlib_test.vivado_simlib, "_execute_ghdl", autospec=True
        ) as execute_ghdl, patch(
            "tsfpga.vivado.simlib_ghdl.system_is_windows", autospec=True
        ) as system_is_windows:
            system_is_windows.return_value = is_windows

            simlib_test.vivado_simlib._compile_ghdl(vhd_files=vhd_files, library_name=library_name)

            assert execute_ghdl.call_args_list == expected_calls

    def get_expected_call(files):
        return call(
            workdir=simlib_test.vivado_simlib.output_path / library_name,
            library_name=library_name,
            files=files,
        )

    # One call with many files on e.g. Linux.
    expected_calls = [
        get_expected_call(
            files=[
                str(vhd_files[0]),
                str(vhd_files[1]),
            ]
        )
    ]
    run_test(is_windows=False, expected_calls=expected_calls)

    # Many calls with individual file on Windows.
    expected_calls = [
        get_expected_call(files=[str(vhd_files[0])]),
        get_expected_call(files=[str(vhd_files[1])]),
    ]
    run_test(is_windows=True, expected_calls=expected_calls)
