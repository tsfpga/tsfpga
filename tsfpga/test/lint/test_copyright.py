# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import re

# Third party libraries
import pytest

# First party libraries
import tsfpga
from tsfpga.git_utils import find_git_files
from tsfpga.system_utils import create_file, read_file


class CopyrightHeader:
    separator_line_length = 100

    def __init__(self, file, copyright_holder, copyright_text_lines=None):
        self._file = file
        self.comment_character = self._get_comment_character()
        self.separator_line = f"{self.comment_character} " + "-" * (
            self.separator_line_length - 1 - len(self.comment_character)
        )
        self.expected_copyright_header = self._get_expected_copyright_header(
            copyright_holder, copyright_text_lines
        )

    def check_file(self):
        """
        Copyright comments should be correct. It should be followed by a blank line or another
        comment.
        """
        copyright_header_re = self.expected_copyright_header.replace("(", "\\(").replace(")", "\\)")
        regexp = re.compile(copyright_header_re + rf"($|\n|{self.comment_character})")
        data = read_file(self._file)
        return regexp.match(data) is not None

    def fix_file(self):
        if self._is_suitable_for_insertion():
            self._insert_copyright_header()
        else:
            raise ValueError(f"Can not fix copyright header in file {self._file}")

    def _get_expected_copyright_header(self, copyright_holder, copyright_text_lines):
        header = f"{self.separator_line}\n"
        header += (
            f"{self.comment_character} Copyright (c) {copyright_holder}. All rights reserved.\n"
        )
        if copyright_text_lines:
            header += f"{self.comment_character}\n"
            for copyright_text_line in copyright_text_lines:
                header += f"{self.comment_character} {copyright_text_line}\n"
        header += f"{self.separator_line}\n"
        return header

    def _get_comment_character(self):
        if self._file.name.endswith(".py"):
            return "#"
        if self._file.name.endswith(".vhd"):
            return "--"
        if self._file.name.endswith((".xdc", ".tcl")):
            return "#"
        if self._file.name.endswith((".c", ".cpp", ".h", ".v")):
            return "//"
        raise RuntimeError(f"Could not decide file ending of {self._file}")

    def _is_suitable_for_insertion(self):
        """
        If the file does not begin with a comment, we consired it suitable to insert a new copyright
        header comment.
        """
        return not read_file(self._file).startswith(self.comment_character)

    def _insert_copyright_header(self):
        data = read_file(self._file)
        data = f"{self.expected_copyright_header}\n{data}"
        create_file(self._file, data)


def files_to_check_for_copyright_header():
    file_endings = (".py", ".vhd", ".tcl")
    exclude_directories = [tsfpga.TSFPGA_EXAMPLE_MODULES / "artyz7" / "tcl"]
    for file_ending in file_endings:
        for file in find_git_files(
            directory=tsfpga.REPO_ROOT,
            exclude_directories=exclude_directories,
            file_endings_include=file_ending,
        ):
            yield file


def test_copyright_header_of_all_checked_in_files():
    test_ok = True
    for file in files_to_check_for_copyright_header():
        copyright_lines = [
            "This file is part of the tsfpga project, a project platform for modern "
            "FPGA development.",
            "https://tsfpga.com",
            "https://gitlab.com/tsfpga/tsfpga",
        ]
        copyright_header_checker = CopyrightHeader(file, "Lukas Vik", copyright_lines)

        if not copyright_header_checker.check_file():
            test_ok = False
            print(
                f"Fail for {file}\nExpected:\n{copyright_header_checker.expected_copyright_header}"
            )

    assert test_ok


def test_check_file(tmp_path):
    header = "-- " + "-" * 97 + "\n"
    header += "-- Copyright (c) Apa. All rights reserved.\n"
    header += "-- " + "-" * 97 + "\n"

    file = create_file(tmp_path / "header.vhd", header)
    copyright_header = CopyrightHeader(file, "Apa")
    assert copyright_header.check_file()

    file = create_file(tmp_path / "non_comment.vhd", header + "non-comment on line after")
    copyright_header = CopyrightHeader(file, "Apa")
    assert not copyright_header.check_file()

    file = create_file(tmp_path / "empty_line.vhd", header + "\nEmpty line and then non-comment")
    copyright_header = CopyrightHeader(file, "Apa")
    assert copyright_header.check_file()

    file = create_file(tmp_path / "further_comment.vhd", header + "-- Further comment\n")
    copyright_header = CopyrightHeader(file, "Apa")
    assert copyright_header.check_file()


def test_check_file_with_copyright_text(tmp_path):
    header = "-- " + "-" * 97 + "\n"
    header += "-- Copyright (c) Apa. All rights reserved.\n"
    header += "--\n"
    header += "-- Some more\n"
    header += "-- text.\n"
    header += "-- " + "-" * 97 + "\n"

    file = create_file(tmp_path / "header.vhd", header)
    copyright_header = CopyrightHeader(file, "Apa", ["Some more", "text."])
    assert copyright_header.check_file()


def test_fix_file_comment_insertion(tmp_path):
    data = "Apa\n"
    file = create_file(tmp_path / "file_for_test.vhd", data)

    copyright_header = CopyrightHeader(file, "Hest Hestsson")
    copyright_header.fix_file()

    data = read_file(file).split("\n")
    assert data[0] == "-- " + "-" * 97
    assert data[1] == "-- Copyright (c) Hest Hestsson. All rights reserved."
    assert data[2] == "-- " + "-" * 97
    assert data[3] == ""
    assert data[4] == "Apa"


def test_fix_file_should_not_run_on_dirty_file(tmp_path):
    data = "-- Custom comment line\n\nApa\n"
    file = create_file(tmp_path / "file_for_test.vhd", data)
    copyright_header = CopyrightHeader(file, "A")

    with pytest.raises(ValueError) as exception_info:
        copyright_header.fix_file()
    assert str(exception_info.value) == f"Can not fix copyright header in file {file}"
