# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# A set of methods for building sphinx docs. Should be reusable between projects.
# --------------------------------------------------------------------------------------------------

# Standard libraries
import sys
from datetime import datetime
from subprocess import check_call

# Third party libraries
from git import Repo
from packaging.version import parse

# First party libraries
from tsfpga.system_utils import read_file


def generate_release_notes(repo_root, release_notes_directory, project_name):
    """
    Generate release notes in RST format based on a directory full of release note files.
    Will match each file to a git tag.

    Arguments:
        repo_root (pathlib.Path): Git commands will be executed here.
        release_notes_directory (pathlib.Path): Location of release notes files.
        project_name (str): Name of project will be used for the gitlab link.

    Return:
        str: RST code with release notes.
    """
    rst = ""

    for release, previous_release_git_tag in _get_release_notes_files(
        repo_root=repo_root, release_notes_directory=release_notes_directory
    ):
        heading = f"{release.version} ({release.date})"
        rst += heading + "\n"
        rst += "-" * len(heading) + "\n"
        rst += "\n"
        if previous_release_git_tag is not None:
            diff_url = (
                f"https://gitlab.com/tsfpga/{project_name}/-/compare/"
                f"{previous_release_git_tag}...{release.git_tag}"
            )
            rst += f"`Changes since previous release <{diff_url}>`__\n"
        rst += "\n"
        rst += read_file(release.release_notes_file)
        rst += "\n"

    return rst


def _get_release_notes_files(repo_root, release_notes_directory):
    """
    Iterate the release notes.
    """
    unreleased_notes_file = release_notes_directory / "unreleased.rst"

    release_notes = []

    # Get all versioned release notes files and sort them in order newest -> oldest
    for release_notes_file in release_notes_directory.glob("*.rst"):
        if not release_notes_file == unreleased_notes_file:
            release_notes.append(release_notes_file)

    # Sort by parsing the version number in the file name. Newest to oldest.
    def sort_key(path):
        return parse(path.stem)

    release_notes.sort(key=sort_key, reverse=True)

    # The "Unreleased" shall be first
    release_notes.insert(0, unreleased_notes_file)

    repo = Repo(repo_root)
    releases = [
        Release(repo=repo, release_notes_file=release_notes_file)
        for release_notes_file in release_notes
    ]

    for idx, release in enumerate(releases):
        if idx == len(releases) - 1:
            previous_release_git_tag = None
        else:
            previous_release_git_tag = releases[idx + 1].git_tag

        yield release, previous_release_git_tag


class Release:
    """
    Used to represent a release.
    """

    def __init__(self, repo, release_notes_file):
        self.release_notes_file = release_notes_file

        version = release_notes_file.stem
        if version == "unreleased":
            self.version = "Unreleased"
            self.git_tag = "main"
            self.date = "YYYY-MM-DD"
        else:
            self.version = version
            self.git_tag = "v" + self.version
            self.date = self.get_git_date_from_tag(repo=repo, tag=self.git_tag)

    @staticmethod
    def get_git_date_from_tag(repo, tag):
        """
        Get a formatted date string, gathered from git log based on tag name.
        """
        timestamp = repo.tag(f"refs/tags/{tag}").commit.committed_date
        time = datetime.fromtimestamp(timestamp)
        return f"{time.day} {time:%B} {time.year}".lower()


def build_sphinx(build_path, output_path):
    """
    Execute sphinx on command line to build HTML documentation.

    Arguments:
        build_path (pathlib.Path): The location that contains ``conf.py`` and ``index.rst``.
        output_path (pathlib.Path): Where to place the generated HTML.
    """
    # Since we set the working directory when making the system call, the paths must be absolute
    build_path = build_path.resolve()
    output_path = output_path.resolve()

    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        # Enable nitpicky mode
        "-n",
        # Turn errors into warnings
        "-W",
        # Show full traceback upon error
        "-T",
        str(build_path),
        str(output_path),
    ]
    check_call(cmd, cwd=build_path)

    index_html = output_path / "index.html"
    assert index_html.exists(), index_html
    print(f"Open with:\nfirefox {index_html} &")
