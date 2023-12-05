# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import subprocess
from pathlib import Path

# Third party libraries
import pytest

# First party libraries
from tsfpga.system_utils import (
    create_directory,
    create_file,
    delete,
    path_relative_to,
    read_last_lines_of_file,
    run_command,
)


def test_delete_files_and_folders(tmp_path):
    # Test deleting a file, with and without wait
    path = create_file(tmp_path / "temp.txt")
    assert path.exists()
    delete(path)
    assert not path.exists()

    path = create_file(tmp_path / "temp.txt")
    assert path.exists()
    delete(path, wait_until_deleted=True)
    assert not path.exists()

    # Test deleting a directory, with and without wait
    path = create_directory(tmp_path / "temp_dir")
    assert path.exists()
    delete(path)
    assert not path.exists()

    path = create_directory(tmp_path / "temp_dir")
    assert path.exists()
    delete(path, wait_until_deleted=True)
    assert not path.exists()


def test_path_relative_to():
    this_file = Path(__file__)
    this_dir = this_file.parent
    parent = this_dir.parent

    assert path_relative_to(this_file, this_dir) == Path(this_file.name)
    assert path_relative_to(this_file, parent) == Path(this_dir.name) / this_file.name
    assert (
        path_relative_to(this_file, parent / "whatever")
        == Path("..") / this_dir.name / this_file.name
    )


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


def test_run_command_should_capture_output_as_strings():
    this_dir = Path(__file__).parent.resolve()

    cmd = ["ls", str(this_dir)]
    result = run_command(cmd, capture_output=True)

    assert isinstance(result.stdout, str)
    assert isinstance(result.stderr, str)

    assert result.stderr == ""

    print(result.stdout)
    print(result.stderr)

    # Show that it is regular text with regular newlines.
    assert "\ntest_system_utils.py\n" in result.stdout
    assert "\ntest_ip_core_file.py\n" in result.stdout
