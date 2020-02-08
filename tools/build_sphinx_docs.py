# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from glob import glob
from os.path import abspath, basename, dirname, exists, join, splitext
from subprocess import check_call, check_output
import sys


REPO_ROOT = abspath(join(dirname(__file__), ".."))
sys.path.append(REPO_ROOT)
import tsfpga
from tsfpga.system_utils import create_file, read_file


def main():
    generate_registers()
    generate_release_notes()
    build_documentation()


def generate_registers():
    cmd = [
        sys.executable,
        join(tsfpga.TSFPGA_EXAMPLES, "build.py"),
        "--generate-registers-only",
    ]
    check_call(cmd)


def generate_release_notes():
    rst = """
Release notes
=============

"""

    for version, date, release_notes_file in get_release_notes_files():
        heading = f"[{version}] - {date}"
        rst += heading + "\n"
        rst += "-" * len(heading) + "\n"
        rst += "\n"
        rst += read_file(release_notes_file)
        rst += "\n"

    create_file(join(tsfpga.TSFPGA_DOC, "sphinx", "release_notes.rst"), rst)


def get_release_notes_files():
    release_notes_dir = join(tsfpga.TSFPGA_DOC, "release_notes")
    unreleased_notes_file = join(release_notes_dir, "unreleased.rst")

    release_notes = []

    # Get all versioned release notes files and sort them in order newest -> oldest
    for release_notes_file in glob(join(release_notes_dir, "*.rst")):
        if not release_notes_file == unreleased_notes_file:
            release_notes.append(release_notes_file)
    release_notes.sort(reverse=True)

    # The "Unreleased" shall be first
    if exists(unreleased_notes_file):
        release_notes.insert(0, unreleased_notes_file)

    for release_notes_file in release_notes:
        if release_notes_file == unreleased_notes_file:
            version = "Unreleased"
            date = "YYYY-MM-DD"
        else:
            version = splitext(basename(release_notes_file))[0]
            date = get_git_date_from_tag("v" + version)

        yield version, date, release_notes_file


def get_git_date_from_tag(tag):
    cmd = [
        "git",
        "show",
        "-s",
        "--format=%cd",
        "--date=short",
        tag
    ]
    return check_output(cmd).decode().strip()


def build_documentation():
    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        "-EanWT",
        join(tsfpga.TSFPGA_DOC, "sphinx"),
        join(REPO_ROOT, "generated", "sphinx_html"),
    ]
    check_call(cmd)


if __name__ == "__main__":
    main()
