# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# First party libraries
from tsfpga import REPO_ROOT, TSFPGA_DOC, TSFPGA_EXAMPLE_MODULES, TSFPGA_TCL
from tsfpga.git_utils import find_git_files
from tsfpga.test.lint.file_format_lint import (
    check_file_ends_with_newline,
    check_file_for_carriage_return,
    check_file_for_line_length,
    check_file_for_tab_character,
    check_file_for_trailing_whitespace,
    open_file_with_encoding,
)


def test_all_checked_in_files_are_properly_encoded():
    """
    To avoid problems with different editors and different file encodings, all checked in files
    should contain only ASCII characters.

    Avoid one of the documentation files that uses wonky characters to illustrate a directory tree.
    """
    for file in files_to_test(exclude_directories=[TSFPGA_DOC / "sphinx" / "module_structure.rst"]):
        open_file_with_encoding(file)


def test_all_checked_in_files_end_with_newline():
    """
    All checked in non-empty files should end with a UNIX style line break (\n).
    Otherwise UNIX doesn't consider them actual text files.
    """
    test_ok = True
    for file in files_to_test():
        test_ok &= check_file_ends_with_newline(file)
    assert test_ok


def test_no_checked_in_files_contain_tabs():
    """
    To avoid problems with files looking different in different editors, no checked in files may
    contain TAB characters.
    """
    test_ok = True
    for file in files_to_test():
        test_ok &= check_file_for_tab_character(file)
    assert test_ok


def test_no_checked_in_files_contain_carriage_return():
    """
    All checked in files should use UNIX style line breaks (\n not \r\n).
    Some Linux editors and tools will display or interpret the \r as something other than a line
    break.
    """
    test_ok = True
    for file in files_to_test():
        test_ok &= check_file_for_carriage_return(file)
    assert test_ok


def test_no_checked_in_files_contain_trailing_whitespace():
    """
    Trailing whitespace is not allowed. Some motivation here:
    https://softwareengineering.stackexchange.com/questions/121555/
    """
    test_ok = True
    excludes = [
        # From Vivado, not modified by us
        TSFPGA_EXAMPLE_MODULES
        / "artyz7"
        / "tcl"
        / "block_design.tcl",
    ]
    for file in files_to_test(exclude_directories=excludes):
        test_ok &= check_file_for_trailing_whitespace(file)
    assert test_ok


def test_no_checked_in_files_have_too_long_lines():
    test_ok = True
    excludes = [
        # Can not break long commands on Windows.
        REPO_ROOT / ".github" / "workflows" / "ci.yml",
        # RST syntax hard to break.
        REPO_ROOT / "readme.rst",
        TSFPGA_DOC / "release_notes" / "12.2.0.rst",
        TSFPGA_DOC / "release_notes" / "12.3.0.rst",
        TSFPGA_DOC / "sphinx" / "hdl_registers.rst",
        # We list the license text exactly as the original, with no line breaks
        REPO_ROOT / "license.txt",
        # Impossible TCL syntax to break
        TSFPGA_TCL / "check_timing.tcl",
        # From Vivado, not modified by us
        TSFPGA_EXAMPLE_MODULES / "artyz7" / "tcl" / "block_design.tcl",
    ]
    for file_path in files_to_test(exclude_directories=excludes):
        test_ok &= check_file_for_line_length(file_path=file_path)

    assert test_ok


def files_to_test(exclude_directories=None):
    # Do not test binary image files
    return find_git_files(
        directory=REPO_ROOT,
        exclude_directories=exclude_directories,
        file_endings_avoid=("png", "svg", "xcf"),
    )
