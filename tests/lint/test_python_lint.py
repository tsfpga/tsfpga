# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import sys

import tsfpga
from tsfpga.system_utils import run_command


def _run_ruff(command: list[str]):
    run_command([sys.executable, "-m", "ruff", *command], cwd=tsfpga.REPO_ROOT)


def test_ruff_check():
    _run_ruff(command=["check"])


def test_ruff_format():
    _run_ruff(command=["format", "--check", "--diff"])
