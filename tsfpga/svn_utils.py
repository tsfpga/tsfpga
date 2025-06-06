# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

from .system_utils import file_is_in_directory, run_command

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def get_svn_revision_information(cwd: Path | None = None, use_rst_annotation: bool = False) -> str:
    """
    Get a string describing the current SVN commit.
    E.g. ``"r1234"`` or ``"r1234 (local changes present)"``.

    Arguments:
        cwd: The directory where SVN commands will be run.
        use_rst_annotation: Use reStructuredText literal annotation for the revision value.
    """
    check_that_svn_commands_are_available(cwd=cwd)

    annotation = "``" if use_rst_annotation else ""
    revision = f"r{get_svn_revision(cwd=cwd)}"
    result = f"{annotation}{revision}{annotation}"

    if svn_local_changes_are_present(cwd=cwd):
        result += " (local changes present)"

    return result


def svn_commands_are_available(cwd: Path | None = None) -> bool:
    """
    True if "svn" command executable is available and ``cwd`` is in a valid SVN repo.

    Arguments:
        cwd: The directory where SVN commands will be run.
    """
    try:
        get_svn_revision(cwd=cwd)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return True


def check_that_svn_commands_are_available(cwd: Path | None = None) -> None:
    """
    Raise an exception unless "svn" command executable is available and ``cwd`` is in a valid
    SVN repo.

    Arguments:
        cwd: The directory where SVN commands will be run.
    """
    if not svn_commands_are_available(cwd):
        message = (
            "Could not run SVN. Is the command available on PATH? Is the script called from a repo?"
        )
        raise RuntimeError(message)


def get_svn_revision(cwd: Path | None = None) -> int:
    """
    Get the current SVN revision number.

    Arguments:
        cwd: The directory where SVN commands will be run.
    """
    command = ["svn", "info", "--show-item", "revision"]
    stdout: str = run_command(cmd=command, cwd=cwd, capture_output=True).stdout

    # Remove trailing newline
    return int(stdout.strip())


def svn_local_changes_are_present(cwd: Path | None = None) -> bool:
    """
    Return true if the repo contains changes that have been made after the last commit.
    Info from here: https://rubyinrails.com/2014/01/11/svn-command-to-check-modified-files/

    Arguments:
        cwd: The directory where SVN commands will be run.
    """
    command = ["svn", "status"]
    stdout: str = run_command(cmd=command, cwd=cwd, capture_output=True).stdout

    # Status code for file Added, Deleted, Modified, in Conflict or missing
    regexp = re.compile(r"\n[ADMC!] ")
    return regexp.search(stdout) is not None


RE_SVN_STATUS_LINE = re.compile(r"^.+\d+\s+\d+\s+\S+\s+(\S+)$")


def find_svn_files(
    directory: Path,
    excludes: list[Path] | None = None,
    file_endings_include: str | tuple[str, ...] | None = None,
    file_endings_avoid: str | tuple[str, ...] | None = None,
) -> Iterable[Path]:
    """
    Find files that are checked in to SVN. It runs "svn status" rather than "svn ls". This means
    that it is a local operation, that does not require credentials or any connection with
    an SVN server.

    Arguments:
        directory: Search in this directory.
        excludes: These files and folders will not be included.
        file_endings_include: Only files with these endings will be included.
        file_endings_avoid: Files with these endings will not be included.

    Return:
        The files that are available in SVN.
    """
    excludes = [] if excludes is None else [exclude.resolve() for exclude in excludes]

    command = ["svn", "status", "-v"]
    stdout = run_command(cmd=command, cwd=directory, capture_output=True).stdout

    for line in stdout.split("\n"):
        match = RE_SVN_STATUS_LINE.match(line)
        if not match:
            continue

        svn_file = match.group(1)
        file_path = directory / svn_file

        if not file_path.exists():
            raise FileNotFoundError(f"Error when concatenating relative paths: {file_path}")

        if file_path.is_dir():
            continue

        if file_endings_include is not None and not file_path.name.endswith(file_endings_include):
            continue

        if file_endings_avoid is not None and file_path.name.endswith(file_endings_avoid):
            continue

        if file_is_in_directory(file_path, excludes):
            continue

        yield file_path
