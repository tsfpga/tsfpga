# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path

# Third party libraries
import pytest

# First party libraries
from tsfpga import DEFAULT_FILE_ENCODING
from tsfpga.system_utils import create_file


def open_file_with_encoding(file: Path) -> None:
    """
    Try to open the ``file`` with ASCII encoding.
    If that fails, i.e. if it contains non-ASCII characters, print information and raise exception.
    """
    try:
        with open(file, encoding="ascii") as file_handle:
            file_handle.read()

    except UnicodeDecodeError as exception:
        print(file)
        with open(file, encoding="utf8") as file_handle:
            lines = file_handle.readlines()

        for line_idx, line in enumerate(lines):
            for character in line:
                try:
                    character.encode("ascii")
                except UnicodeEncodeError:
                    print(f"Character {character} on line {line_idx + 1} is not ASCII")

        raise exception


def check_file_ends_with_newline(file: Path) -> bool:
    """
    Return True if ``file`` ends with newline.
    """
    test_ok = True
    with open(file, encoding=DEFAULT_FILE_ENCODING) as file_handle:
        file_data = file_handle.read()
        if len(file_data) != 0:
            if file_data[-1] != "\n":
                print(f"File {file} didn't end with newline")
                test_ok = False

    return test_ok


def check_file_for_tab_character(file: Path) -> bool:
    """
    Return True of ``file`` does not contain any TAB character.
    """
    test_ok = True
    with open(file, encoding=DEFAULT_FILE_ENCODING) as file_handle:
        for idx, line in enumerate(file_handle.readlines()):
            if "\t" in line:
                test_ok = False
                print(f"TAB character (\\t) on line {idx + 1} in {file}")
    return test_ok


def check_file_for_carriage_return(file: Path) -> bool:
    """
    Return True if ``file`` does not contain any carriage return (CR).
    """
    test_ok = True
    with open(file, encoding=DEFAULT_FILE_ENCODING, newline="") as file_handle:
        if "\r" in file_handle.read():
            test_ok = False
            print(f"Windows style line breaks (\\r\\n aka CR/LF) in {file}")

    return test_ok


def check_file_for_trailing_whitespace(file: Path) -> bool:
    """
    Return True if ``file`` does not contain any trailing whitespace.
    """
    test_ok = True
    with open(file, encoding=DEFAULT_FILE_ENCODING) as file_handle:
        for idx, line in enumerate(file_handle.readlines()):
            if " \n" in line:
                test_ok = False
                print(f"Trailing whitespace on line {idx + 1} in {file}")

    return test_ok


def check_file_for_line_length(file_path: Path, max_length: int = 100) -> bool:
    """
    Return True if ``file`` does not contain any line that is longer than ``max_length`` characters.
    """
    max_length_with_newline = max_length + 1
    test_ok = True

    with open(file_path, encoding=DEFAULT_FILE_ENCODING) as file_handle:
        lines = file_handle.readlines()
        for line_number, line in enumerate(lines):
            line_length = len(line)
            if line_length > max_length_with_newline:
                print(
                    f"Line {file_path}:{line_number + 1} is too long "
                    f"({line_length - 1} > {max_length_with_newline - 1})"
                )
                test_ok = False

    return test_ok


def test_open_file_with_encoding_should_raise_exception_on_bad_file(tmp_path: Path) -> None:
    """
    Sanity check that the function we use actually triggers on bad files.
    """
    file = tmp_path / "temp_file_for_test.txt"
    with open(file, "w", encoding="utf-8") as file_handle:
        # Swedish word for island = non-ASCII character
        data = "\N{LATIN CAPITAL LETTER O WITH DIAERESIS}"
        file_handle.write(data)

    with pytest.raises(UnicodeDecodeError):
        open_file_with_encoding(file)


def test_check_file_for_tab_character_should_fail_on_bad_file(tmp_path: Path) -> None:
    """
    Sanity check that the function we use actually triggers on bad files.
    """
    data = "Apa\thest"
    file = create_file(tmp_path / "temp_file_for_test.txt", data)
    assert not check_file_for_tab_character(file)


def test_check_file_for_carriage_return_should_fail_on_bad_file(tmp_path: Path) -> None:
    """
    Sanity check that the function we use actually triggers on bad files.
    """
    file = tmp_path / "temp_file_for_test.txt"
    data = b"Apa\r\nhest"
    with file.open("wb") as file_handle:
        file_handle.write(data)
    assert not check_file_for_carriage_return(file)


def test_check_file_for_trailing_whitespace(tmp_path: Path) -> None:
    """
    Sanity check that the function we use actually triggers on bad files.
    """
    data = "Apa \nhest    \nzebra"
    file = create_file(tmp_path / "temp_file_for_test.txt", data)
    assert not check_file_for_trailing_whitespace(file)


def test_check_file_for_line_length(tmp_path: Path) -> None:
    """
    Sanity check that the function we use actually triggers on bad files.
    """
    ok_data = """
asdf
apa
hest
"""
    ok_file_path = create_file(tmp_path / "ok_data.txt", contents=ok_data)
    assert check_file_for_line_length(ok_file_path)

    bad_data = """
asdf
apa apa apa apa apa apa apa apa apa apa apa apa apa apa apa apa apa apa apa apa apa apa apa apa
hest
"""
    bad_file_path = create_file(tmp_path / "bad_data.txt", contents=bad_data)
    assert not check_file_for_line_length(file_path=bad_file_path, max_length=80)
