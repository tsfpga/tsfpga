# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import join, dirname
import pytest
import unittest

from tsfpga.git_utils import find_git_files
from tsfpga.system_utils import create_file, delete


THIS_DIR = dirname(__file__)


def open_file_with_encoding(file):
    print(file)
    with open(file, "r", encoding="ascii") as file_handle:
        file_handle.read()


def test_all_checked_in_files_are_properly_encoded():
    """
    To avoid problems with different editors and different file encodings, all checked in files should
    contain only ASCII characters.
    """
    for file in find_git_files():
        open_file_with_encoding(file)


def check_file_for_tab_character(file):
    test_ok = True
    with open(file) as file_handle:
        for idx, line in enumerate(file_handle.readlines()):
            if "\t" in line:
                test_ok = False
                print("TAB charatcher (\\t) on line %i in %s" % (idx + 1, file))
    return test_ok


def test_no_checked_in_files_contain_tabs():
    """
    To avoid problems with files looking different in different editors, no checked in files may
    contain TAB characters.
    """
    test_ok = True
    for file in find_git_files():
        test_ok &= check_file_for_tab_character(file)
    assert test_ok


def check_file_for_carriage_return(file):
    test_ok = True
    with open(file, newline="") as file_handle:
        if "\r" in file_handle.read():
            test_ok = False
            print("Windows style line breaks (\\r\\n aka CR/LF) in " + file)
    return test_ok


def test_no_checked_in_files_contain_carriage_return():
    """
    All checked in files should use UNIX style line breaks (\n not \r\n).
    Some Linux editors and tools will display or interpret the \r as something other than a line break.
    """
    test_ok = True
    for file in find_git_files():
        test_ok &= check_file_for_carriage_return(file)
    assert test_ok


def check_file_for_trailing_whitespace(file):
    test_ok = True
    with open(file) as file_handle:
        for idx, line in enumerate(file_handle.readlines()):
            if " \n" in line:
                test_ok = False
                print("Trailing whitespace on line %i in %s" % (idx + 1, file))
    return test_ok


def test_no_checked_in_files_contain_trailing_whitespace():
    """
    Trailing whitespace is not allowed.
    Some motivation here: https://softwareengineering.stackexchange.com/questions/121555/why-is-trailing-whitespace-a-big-deal
    """
    test_ok = True
    for file in find_git_files():
        test_ok &= check_file_for_trailing_whitespace(file)
    assert test_ok


class TestFileFormat(unittest.TestCase):

    file = join(THIS_DIR, "temp_file_for_test.txt")

    def setUp(self):
        delete(self.file)

    def test_open_file_with_encoding_should_raise_exception_on_bad_file(self):
        """
        Sanity check that the function we use actually triggers on bad files.
        """
        with open(self.file, "w", encoding="utf-8") as file_handle:
            data = "\N{LATIN CAPITAL LETTER O WITH DIAERESIS}"  # Swedish word for island = non-ASCII character
            file_handle.write(data)

        with pytest.raises(UnicodeDecodeError):
            open_file_with_encoding(self.file)

    def test_check_file_for_tab_character_should_fail_on_bad_file(self):
        """
        Sanity check that the function we use actually triggers on bad files.
        """
        data = "Apa\thest"
        create_file(self.file, data)
        assert not check_file_for_tab_character(self.file)

    def test_check_file_for_carriage_return_should_fail_on_bad_file(self):
        """
        Sanity check that the function we use actually triggers on bad files.
        """
        data = b"Apa\r\nhest"
        with open(self.file, "wb") as file_handle:
            file_handle.write(data)
        assert not check_file_for_carriage_return(self.file)

    def test_check_file_for_trailing_whitespace(self):
        """
        Sanity check that the function we use actually triggers on bad files.
        """
        data = "Apa \nhest    \nzebra"
        create_file(self.file, data)
        assert not check_file_for_trailing_whitespace(self.file)
