# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import subprocess

import pytest

from tsfpga.system_utils import create_file, read_last_lines_of_file, run_command


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


def test_read_last_lines_of_file_with_short_file(tmp_path):
    # A file that is smaller than the buffer size
    data = "a\nb\nc"
    file = create_file(tmp_path / "data.txt", contents=data)
    assert read_last_lines_of_file(file, num_lines=10) == data


def test_read_last_lines_of_file_with_long_file(tmp_path):
    # A file that is larger than the buffer size
    data_trash = (("a" * 700) + "\n") * 3000
    data_last_lines = (("b" * 700) + "\n") * 10
    file = create_file(tmp_path / "data.txt", contents=data_trash + data_last_lines)
    assert read_last_lines_of_file(file, num_lines=10) == data_last_lines


def test_read_last_lines_of_file_with_trailing_newlines(tmp_path):
    # A file that is smaller than the buffer size
    data = "a\nb\n\n  \n\n"
    file = create_file(tmp_path / "data.txt", contents=data)
    assert read_last_lines_of_file(file, num_lines=10) == data


def test_read_last_lines_of_file_with_empty_file(tmp_path):
    data = ""
    file = create_file(tmp_path / "data.txt", contents=data)
    assert read_last_lines_of_file(file, num_lines=10) == data

    data = "\n"
    file = create_file(tmp_path / "data.txt", contents=data)
    assert read_last_lines_of_file(file, num_lines=10) == data
