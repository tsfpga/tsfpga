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

    for release, previous_release_git_tag in get_release_notes_files():
        heading = f"[{release.version}] - {release.date}"
        rst += heading + "\n"
        rst += "-" * len(heading) + "\n"
        rst += "\n"
        if previous_release_git_tag is not None:
            diff_url = f"https://gitlab.com/truestream/tsfpga/-/compare/{previous_release_git_tag}...{release.git_tag}"
            rst += f"`Changes since previous release <{diff_url}>`__\n"
        rst += "\n"
        rst += read_file(release.release_notes_file)
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
    release_notes.insert(0, unreleased_notes_file)

    releases = [Release(release_notes_file) for release_notes_file in release_notes]

    for idx, release in enumerate(releases):
        if idx == len(releases) - 1:
            previous_release_git_tag = None
        else:
            previous_release_git_tag = releases[idx + 1].git_tag

        yield release, previous_release_git_tag


class Release:

    def __init__(self, release_notes_file):
        self.release_notes_file = release_notes_file

        version = splitext(basename(release_notes_file))[0]
        if version == "unreleased":
            self.version = "Unreleased"
            self.git_tag = "master"
            self.date = "YYYY-MM-DD"
        else:
            self.version = version
            self.git_tag = "v" + self.version
            self.date = self.get_git_date_from_tag(self.git_tag)

    @staticmethod
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
