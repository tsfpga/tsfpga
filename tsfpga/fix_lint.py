import re

from tsfpga.git_utils import find_git_files


RE_TRAILING_WHITESPACE = re.compile(" +\n", re.DOTALL)


def fix_trailing_whitespace(file):
    with open(file) as file_handle:
        contents = file_handle.read()

    match = RE_TRAILING_WHITESPACE.search(contents)
    if match:
        print("Fixing trailing whitespace in " + file)
        with open(file, "w") as file_handle:
            file_handle.write(RE_TRAILING_WHITESPACE.sub("\n", contents))


def main():
    for file in find_git_files():
        fix_trailing_whitespace(file)


if __name__ == "__main__":
    main()
