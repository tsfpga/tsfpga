# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import os
import sys

# Third party libraries
import pytest

# First party libraries
import tsfpga
from tsfpga.system_utils import run_command


@pytest.mark.parametrize("vunit_simulator", ["modelsim", "rivierapro", "ghdl"])
def test_hdl_compilation(vunit_simulator, tmp_path):
    """
    Compile all the HDL code, no Vivado involvement. This is a subset of 'test_hdl_test_cases',
    but is much faster.
    """
    command = [
        sys.executable,
        str(tsfpga.TSFPGA_EXAMPLES / "simulate.py"),
        "--output-path",
        str(tmp_path / "vunit_out"),
        "--vivado-skip",
        "--compile",
    ]

    env = os.environ.copy()
    env["VUNIT_SIMULATOR"] = vunit_simulator

    run_command(cmd=command, cwd=str(tmp_path), env=env)


@pytest.mark.parametrize("vunit_simulator", ["modelsim", "rivierapro", "ghdl"])
def test_hdl_test_cases(vunit_simulator, tmp_path):
    """
    Compile all the HDL code and run all tests that do not contain IP cores. No Vivado involvement.
    """
    # Only one license seat for Modelsim and Riviera-PRO
    num_threads = 1 if vunit_simulator != "ghdl" else 12
    command = [
        sys.executable,
        str(tsfpga.TSFPGA_EXAMPLES / "simulate.py"),
        "--output-path",
        str(tmp_path / "vunit_out"),
        "--vivado-skip",
        "--num-threads",
        str(num_threads),
    ]

    env = os.environ.copy()
    env["VUNIT_SIMULATOR"] = vunit_simulator

    run_command(cmd=command, cwd=str(tmp_path), env=env)


@pytest.mark.parametrize("vunit_simulator", ["modelsim", "rivierapro", "ghdl"])
def test_simlib_compilation_and_ip_core_test_cases(vunit_simulator, tmp_path):
    """
    Compile simlib and generate IP core files. Run the test cases that depend on IP cores.
    For GHDL, no tests will be run (but simlib and IP cores will be handled).
    """
    test_filter = "module_with_ip_cores.*"
    command = [
        sys.executable,
        str(tsfpga.TSFPGA_EXAMPLES / "simulate.py"),
        "--output-path",
        str(tmp_path / "vunit_out"),
        "--output-path-vivado",
        str(tmp_path),
        "--minimal",
        test_filter,
    ]

    env = os.environ.copy()
    env["VUNIT_SIMULATOR"] = vunit_simulator

    run_command(cmd=command, cwd=str(tmp_path), env=env)
