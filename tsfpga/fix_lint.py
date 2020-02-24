# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import argparse
from pathlib import Path
import re
import sys

PATH_TO_TSFPGA = Path(__file__).parent.parent
sys.path.append(str(PATH_TO_TSFPGA.resolve()))

from tsfpga.git_utils import find_git_files
from tsfpga.system_utils import create_file, read_file
from tsfpga.test.lint.test_copyright import CopyrightHeader, files_to_check_for_copyright_header


RE_TRAILING_WHITESPACE = re.compile(" +\n", re.DOTALL)
RE_TAB = re.compile("\t", re.DOTALL)


def fix_trailing_whitespace(file):
    contents = read_file(file)

    if RE_TRAILING_WHITESPACE.search(contents):
        print(f"Fixing trailing whitespace in {file}")
        create_file(file, RE_TRAILING_WHITESPACE.sub("\n", contents))


def fix_tabs(file, tab_width):
    contents = read_file(file)

    if RE_TAB.search(contents):
        print(f"Fixing tabs in {file}")
        replacement = " " * tab_width
        create_file(file, RE_TAB.sub(replacement, contents))


def fix_lint(files, tab_width):
    for file in files:
        fix_trailing_whitespace(file)
        fix_tabs(file, tab_width)


def arguments():
    parser = argparse.ArgumentParser("Automatically fix some lint problems")
    parser.add_argument("--tab-width", type=int, default=2, help="number of spaces to use when replacing tab characters")
    parser.add_argument("files", nargs="*", help="fixup these specific files")
    return parser.parse_args()


def main():
    args = arguments()

    files = args.files if args.files else list(find_git_files(file_endings_avoid=(".png")))
    fix_lint(files, args.tab_width)

    files = args.files if args.files else list(files_to_check_for_copyright_header())
    for filename in files:
        copyright_header = CopyrightHeader("Lukas Vik", filename)
        if not copyright_header.check_file():
            copyright_header.fix_file()


if __name__ == "__main__":
    main()
