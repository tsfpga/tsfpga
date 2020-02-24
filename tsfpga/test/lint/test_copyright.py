# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import re

import pytest

from tsfpga import TSFPGA_EXAMPLE_MODULES
from tsfpga.system_utils import create_file, read_file
from tsfpga.git_utils import find_git_files


class CopyrightHeader:

    def __init__(self, copyright_holder, file):
        self._copyright_holder = copyright_holder
        self._file = file

    def check_file(self):
        """
        Copyright comments should be correct. It should be followed by a blank line or another comment.
        """
        copyright_header_re = self.get_expected_copyright_header().replace("(", "\\(").replace(")", "\\)")
        regexp = re.compile(copyright_header_re + rf"($|\n|{self._comment_character})")
        data = read_file(self._file)
        return regexp.match(data) is not None

    def get_expected_copyright_header(self):
        separator_line = self._comment_character + " " + "-" * (79 - len(self._comment_character))
        header = separator_line + "\n" + \
            self._comment_character + " " + f"Copyright (c) {self._copyright_holder}. All rights reserved." + "\n" + \
            separator_line + "\n"
        return header

    def fix_file(self):
        if self._is_suitable_for_insertion():
            self._insert_copyright_header()
        else:
            raise ValueError(f"Can not fix copyright header in file {self._file}")

    @property
    def _comment_character(self):
        if self._file.name.endswith(".py"):
            return "#"
        if self._file.name.endswith(".vhd"):
            return "--"
        if self._file.name.endswith(".tcl"):
            return "#"
        raise RuntimeError(f"Could not decide file ending of {self._file}")

    def _is_suitable_for_insertion(self):
        """
        If the file does not begin with a comment, we consired it suitable to insert a new copyright header comment.
        """
        return not read_file(self._file).startswith(self._comment_character)

    def _insert_copyright_header(self):
        data = read_file(self._file)
        data = self.get_expected_copyright_header() + "\n" + data
        create_file(self._file, data)


def files_to_check_for_copyright_header():
    file_endings = (".py", ".vhd", ".tcl")
    exclude_directories = [TSFPGA_EXAMPLE_MODULES / "artyz7" / "tcl"]
    for file_ending in file_endings:
        for file in find_git_files(file_endings_include=file_ending, exclude_directories=exclude_directories):
            yield file


def test_copyright_header_of_all_checked_in_files():
    test_ok = True
    for file in files_to_check_for_copyright_header():
        copyright_header_checker = CopyrightHeader("Lukas Vik", file)
        if not copyright_header_checker.check_file():
            test_ok = False
            expected = copyright_header_checker.get_expected_copyright_header()
            print(f"Fail for {file}.\nExpected:\n{expected}")
    assert test_ok


def test_check_file(tmp_path):
    header = "-- " + "-" * 77 + "\n"
    header += "-- Copyright (c) Apa. All rights reserved.\n"
    header += "-- " + "-" * 77 + "\n"

    file = create_file(tmp_path / "header.vhd", header)
    copyright_header = CopyrightHeader("Apa", file)
    assert copyright_header.check_file()

    file = create_file(tmp_path / "non_comment.vhd", header + "non-comment on line after")
    copyright_header = CopyrightHeader("Apa", file)
    assert not copyright_header.check_file()

    file = create_file(tmp_path / "empty_line.vhd", header + "\nEmpty line and then non-comment")
    copyright_header = CopyrightHeader("Apa", file)
    assert copyright_header.check_file()

    file = create_file(tmp_path / "further_comment.vhd", header + "-- Further comment\n")
    copyright_header = CopyrightHeader("Apa", file)
    assert copyright_header.check_file()


def test_fix_file_comment_insertion(tmp_path):
    data = "Apa\n"
    file = create_file(tmp_path / "file_for_test.vhd", data)

    copyright_header = CopyrightHeader("Hest Hestsson", file)
    copyright_header.fix_file()

    data = read_file(file).split("\n")
    assert data[0] == "-- " + "-" * 77
    assert data[1] == "-- Copyright (c) Hest Hestsson. All rights reserved."
    assert data[2] == "-- " + "-" * 77
    assert data[3] == ""
    assert data[4] == "Apa"


def test_fix_file_should_not_run_on_dirty_file(tmp_path):
    data = "-- Custom comment line\n\nApa\n"
    file = create_file(tmp_path / "file_for_test.vhd", data)
    copyright_header = CopyrightHeader("A", file)

    with pytest.raises(ValueError) as exception_info:
        copyright_header.fix_file()
    assert str(exception_info.value) == f"Can not fix copyright header in file {file}"
