# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import join, dirname
import pytest
import re
import unittest

from tsfpga import TSFPGA_EXAMPLES

from tsfpga.system_utils import create_file, read_file, delete
from tsfpga.git_utils import find_git_files


THIS_DIR = dirname(__file__)


class CopyrightHeader:

    def __init__(self, copyright_holder, filename):
        self._copyright_holder = copyright_holder
        self._filename = filename

    def check_file(self):
        """
        Copyright comments should be correct. It should be followed by a blank line or another comment.
        """
        copyright_header_re = self.get_expected_copyright_header().replace("(", "\\(").replace(")", "\\)")
        regexp = re.compile(copyright_header_re + rf"($|\n|{self._comment_character})")
        with open(self._filename) as file_handle:
            data = file_handle.read()
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
            raise ValueError(f"Can not fix copyright header in file {self._filename}")

    @property
    def _comment_character(self):
        if self._filename.endswith(".py"):
            return "#"
        if self._filename.endswith(".vhd"):
            return "--"
        if self._filename.endswith(".tcl"):
            return "#"
        raise RuntimeError(f"Could not decide file ending of {self._filename}")

    def _is_suitable_for_insertion(self):
        """
        If the file does not begin with a comment, we consired it suitable to insert a new copyright header comment.
        """
        with open(self._filename) as file_handle:
            return not file_handle.readline().startswith(self._comment_character)

    def _insert_copyright_header(self):
        with open(self._filename) as file_handle:
            data = file_handle.read()
        data = self.get_expected_copyright_header() + "\n" + data
        with open(self._filename, "w") as file_handle:
            file_handle.write(data)


def files_to_check_for_copyright_header():
    file_endings = [".py", ".vhd", ".tcl"]
    exclude_directories = [join(TSFPGA_EXAMPLES, "modules", "artyz7", "tcl")]
    for file_ending in file_endings:
        for filename in find_git_files(file_ending=file_ending, exclude_directories=exclude_directories):
            yield filename


def test_copyright_header_of_all_checked_in_files():
    test_ok = True
    for filename in files_to_check_for_copyright_header():
        copyright_header_checker = CopyrightHeader("Lukas Vik", filename)
        if not copyright_header_checker.check_file():
            test_ok = False
            expected = copyright_header_checker.get_expected_copyright_header()
            print(f"Fail for {filename}.\nExpected:\n{expected}")
    assert test_ok


class TestCopyright(unittest.TestCase):

    file = join(THIS_DIR, "temp_file_for_test.vhd")

    def setUp(self):
        delete(self.file)

    def test_check_file(self):
        header = "-- " + "-" * 77 + "\n"
        header += "-- Copyright (c) Apa. All rights reserved.\n"
        header += "-- " + "-" * 77 + "\n"

        data = header
        create_file(self.file, data)
        copyright_header = CopyrightHeader("Apa", self.file)
        assert copyright_header.check_file()

        data = header + "non-comment on line after"
        create_file(self.file, data)
        copyright_header = CopyrightHeader("Apa", self.file)
        assert not copyright_header.check_file()

        data = header + "\nEmpty line and then non-comment"
        create_file(self.file, data)
        copyright_header = CopyrightHeader("Apa", self.file)
        assert copyright_header.check_file()

        data = header + "-- Further comment\n"
        create_file(self.file, data)
        copyright_header = CopyrightHeader("Apa", self.file)
        assert copyright_header.check_file()

    def test_fix_file_comment_insertion(self):
        data = "Apa\n"
        create_file(self.file, data)

        copyright_header = CopyrightHeader("Hest Hestsson", self.file)
        copyright_header.fix_file()

        data = read_file(self.file).split("\n")
        assert data[0] == "-- " + "-" * 77
        assert data[1] == "-- Copyright (c) Hest Hestsson. All rights reserved."
        assert data[2] == "-- " + "-" * 77
        assert data[3] == ""
        assert data[4] == "Apa"

    def test_fix_file_should_not_run_on_dirty_file(self):
        data = "-- Custom comment line\n\nApa\n"
        create_file(self.file, data)
        copyright_header = CopyrightHeader("A", self.file)

        with pytest.raises(ValueError) as exception_info:
            copyright_header.fix_file()
        assert str(exception_info.value) == f"Can not fix copyright header in file {self.file}"
