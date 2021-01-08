# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from unittest.mock import patch
from pathlib import Path

from tsfpga.vivado.common import run_vivado_tcl

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
