import os
from os.path import join, dirname
import pytest

from hdl_reuse.system_utils import find_git_files


THIS_DIR = dirname(__file__)


def open_file_with_encoding(file):
    print(file)
    with open(file, "r", encoding="ascii") as file_handle:
        file_handle.readlines()


def test_open_file_with_encoding_should_raise_exception_on_file_with_garbage_characters():
    """
    Sanity check that the function we use actually triggers on bad files.
    """
    file = join(THIS_DIR, "temp_file_for_encoding_test.txt")
    with open(file, "w", encoding="utf-8") as file_handle:
        data = "\N{LATIN CAPITAL LETTER O WITH DIAERESIS}"  # Swedish word for island = non-ASCII character
        file_handle.write(data)

    with pytest.raises(UnicodeDecodeError):
        open_file_with_encoding(file)

    os.remove(file)


def test_all_checked_in_files_are_properly_encoded():
    """
    To avoid problems with different editors and different file encodings, all checked in files should
    contain only ASCII characters.
    """
    for file in find_git_files():
        open_file_with_encoding(file)
