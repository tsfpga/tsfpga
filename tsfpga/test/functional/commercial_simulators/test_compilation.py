# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import os
import sys

import pytest

import tsfpga
from tsfpga.system_utils import run_command


@pytest.mark.parametrize("vunit_simulator", ["modelsim", "rivierapro", "ghdl"])
def test_compilation(vunit_simulator, tmp_path):
    command = [
        sys.executable,
        str(tsfpga.TSFPGA_EXAMPLES / "simulate.py"),
        "--compile",
        "--temp-dir",
        str(tmp_path),
        "--vivado-skip",
    ]
    env = os.environ.copy()
    env["VUNIT_SIMULATOR"] = vunit_simulator
    run_command(cmd=command, cwd=str(tmp_path), env=env)
