# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# A set of methods for building sphinx docs. Should be reusable between projects.
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

import sys
from datetime import datetime
from subprocess import CalledProcessError
from typing import TYPE_CHECKING

from git.repo import Repo
from packaging.version import Version, parse

from tsfpga.system_utils import read_file, run_command

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def generate_release_notes(
    repo_root: Path, release_notes_directory: Path, project_name: str
) -> str:
    """
    Generate release notes in RST format based on a directory full of release note files.
    Will match each file to a git tag.

    Arguments:
        repo_root: Git commands will be executed here.
        release_notes_directory: Location of release notes files.
        project_name: Name of project will be used for the GitHub link.

    Return:
        RST code with release notes.
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
                f"https://github.com/{project_name}/{project_name}/compare/"
                f"{previous_release_git_tag}...{release.git_tag}"
            )
            rst += f"`Changes since previous release <{diff_url}>`__\n"
        rst += "\n"
        rst += read_file(release.release_notes_file)
        rst += "\n"

    return rst


def _get_release_notes_files(
    repo_root: Path, release_notes_directory: Path
) -> Iterable[tuple[Release, str | None]]:
    """
    Iterate the release notes.
    """
    unreleased_notes_file = release_notes_directory / "unreleased.rst"

    # All versioned release notes files.
    release_notes = [
        release_notes_file
        for release_notes_file in release_notes_directory.glob("*.rst")
        if release_notes_file != unreleased_notes_file
    ]

    # Sort by parsing the version number in the file name. Newest to oldest.
    def sort_key(path: Path) -> Version:
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
        previous_release_git_tag = None if idx == len(releases) - 1 else releases[idx + 1].git_tag

        yield release, previous_release_git_tag


class Release:
    """
    Used to represent a release.
    """

    def __init__(self, repo: Repo, release_notes_file: Path) -> None:
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
    def get_git_date_from_tag(repo: Repo, tag: str) -> str:
        """
        Get a formatted date string, gathered from git log based on tag name.
        """
        timestamp = repo.tag(f"refs/tags/{tag}").commit.committed_date
        # This call will more or less guess the user's timezone.
        # In a general use case this is not reliable, hence the rule, but in our case
        # the date information is not critical in any way.
        # It is just there for extra info.
        # https://docs.astral.sh/ruff/rules/call-datetime-fromtimestamp/
        time = datetime.fromtimestamp(timestamp)  # noqa: DTZ006
        return f"{time.day} {time:%B} {time.year}".lower()


def build_sphinx(build_path: Path, output_path: Path) -> None:
    """
    Execute sphinx on command line to build HTML documentation.

    Arguments:
        build_path: The location that contains ``conf.py`` and ``index.rst``.
        output_path: Where to place the generated HTML.
    """
    # Since we set the working directory when making the system call, paths must be absolute.
    build_path = build_path.resolve()
    output_path = output_path.resolve()

    print("Building Sphinx documentation...")

    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        # Turn warnings into errors.
        "-W",
        # Show full traceback upon error.
        "-T",
        str(build_path),
        str(output_path),
    ]
    try:
        run_command(cmd, cwd=build_path, capture_output=True)
    except CalledProcessError as exception:
        print(f"ERROR: Sphinx build command failed with exit code {exception.returncode}.")
        if exception.stdout:
            print("-" * 80)
            print("ERROR: Command STDOUT:\n")
            print(exception.stdout)
        if exception.stderr:
            print("-" * 80)
            print("ERROR: Command STDERR:\n")
            print(exception.stderr)
        raise

    index_html = output_path / "index.html"
    if not index_html.exists():
        raise FileNotFoundError(f"Creating HTML failed: {index_html}")

    print(f"Documentation build done. Open with:\n  firefox {index_html} &")
