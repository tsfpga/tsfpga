# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# First party libraries
import tsfpga
from tsfpga.git_utils import find_git_files
from tsfpga.test.lint.copyright_lint import CopyrightHeader


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
            "https://github.com/tsfpga/tsfpga",
        ]
        copyright_header_checker = CopyrightHeader(file, "Lukas Vik", copyright_lines)

        if not copyright_header_checker.check_file():
            test_ok = False
            print(
                f"Fail for {file}\nExpected:\n{copyright_header_checker.expected_copyright_header}"
            )

    assert test_ok
