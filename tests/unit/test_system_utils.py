# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import subprocess

import pytest

from tsfpga.system_utils import run_command


def test_run_command_called_with_nonexisting_binary_should_raise_exception():
    cmd = ["/apa/hest/zebra.exe", "foobar"]
    with pytest.raises(FileNotFoundError):
        run_command(cmd)


def test_run_command_with_non_zero_return_code_should_raise_exception():
    cmd = ["ls", "/apa/hest/zebra"]
    with pytest.raises(subprocess.CalledProcessError):
        run_command(cmd)


def test_run_command_called_with_non_list_should_raise_exception():
    cmd = ["ls", "-la"]
    run_command(cmd)

    cmd = "ls -la"
    with pytest.raises(ValueError) as exception_info:
        run_command(cmd)
    assert str(exception_info.value).startswith("Must be called with a list")
