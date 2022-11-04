# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path
from unittest.mock import patch

# First party libraries
from tsfpga.vivado.common import get_git_sha_slv, get_vivado_version, run_vivado_tcl

THIS_DIR = Path(__file__).parent


def test_run_vivado_tcl():
    vivado_path = THIS_DIR / "vivado.exe"
    tcl_file = THIS_DIR / "script.tcl"
    expected_cmd = [
        str(vivado_path.resolve()),
        "-mode",
        "batch",
        "-notrace",
        "-source",
        str(tcl_file.resolve()),
    ]

    with patch("tsfpga.vivado.common.Process") as mocked_process:
        mocked_process.NonZeroExitCode = ValueError
        assert run_vivado_tcl(vivado_path, tcl_file)
        mocked_process.assert_called_once_with(args=expected_cmd, cwd=THIS_DIR)

    with patch("tsfpga.vivado.common.Process") as mocked_process:
        mocked_process.NonZeroExitCode = ValueError
        assert run_vivado_tcl(vivado_path, tcl_file, no_log_file=True)
        mocked_process.assert_called_once_with(
            args=expected_cmd + ["-nojournal", "-nolog"], cwd=THIS_DIR
        )

    with patch("tsfpga.vivado.common.Process") as mocked_process:
        mocked_process.NonZeroExitCode = ValueError
        mocked_process.return_value.consume_output.side_effect = ValueError("Non-zero exit code!")
        assert not run_vivado_tcl(vivado_path, tcl_file, no_log_file=True)


def test_get_vivado_version():
    assert (
        get_vivado_version(vivado_path=Path("/home/lukas/work/Xilinx/Vivado/2021.2/bin/vivado"))
        == "2021.2"
    )


def test_get_git_sha_slv():
    with patch("tsfpga.vivado.common.get_git_sha") as get_git_sha:
        get_git_sha.return_value = "abcdef0123456789"
        assert get_git_sha_slv(git_directory=None) == (
            "10101011110011011110111100000001",
            "00100011010001010110011110001001",
        )

    with patch("tsfpga.vivado.common.get_git_sha") as get_git_sha:
        get_git_sha.return_value = "00abcdef00123400"
        assert get_git_sha_slv(git_directory=None) == (
            "00000000101010111100110111101111",
            "00000000000100100011010000000000",
        )
