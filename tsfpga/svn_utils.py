# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import re
import subprocess

# First party libraries
from tsfpga.system_utils import file_is_in_directory


def get_svn_revision_information(cwd=None):
    check_that_svn_commands_are_available(cwd)
    result = f"r{get_svn_revision(cwd)}"
    if svn_local_changes_are_present(cwd):
        result += " (local changes present)"
    return result


def svn_commands_are_available(cwd=None):
    try:
        get_svn_revision(cwd)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return True


def check_that_svn_commands_are_available(cwd=None):
    if not svn_commands_are_available(cwd):
        mesg = (
            "Could not run svn. Is the command available on PATH? Is the script called from a repo?"
        )
        raise RuntimeError(mesg)


def get_svn_revision(cwd=None):
    command = ["svn", "info", "--show-item", "revision"]
    output = subprocess.check_output(command, cwd=cwd, universal_newlines=True)
    # Remove trailing newline
    return int(output.strip())


def svn_local_changes_are_present(cwd=None):
    """
    Return true if the repo contains changes that have been made after the last commit.
    Info from here: https://rubyinrails.com/2014/01/11/svn-command-to-check-modified-files/
    """
    command = ["svn", "status"]
    output = subprocess.check_output(command, cwd=cwd, universal_newlines=True)
    # Status code for file Added, Deleted, Modified, in Conflict or missing
    regexp = re.compile(r"\n[ADMC!] ")
    return regexp.search(output) is not None


RE_SVN_STATUS_LINE = re.compile(r"^.+\d+\s+\d+\s+\S+\s+(\S+)$")


def find_svn_files(
    directory,
    excludes=None,
    file_endings_include=None,
    file_endings_avoid=None,
):
    """
    Find files that are checked in to SVN. It runs "svn status" rather than "svn ls". This means
    that it is a local operation, that does not require credentials or any connection with
    an SVN server.

    Arguments:
        directory (pathlib.Path): Search in this directory.
        excludes (list(pathlib.Path)): These files and folders will not be included.
        file_endings_include (str or tuple(str)). Only files with these endings will be included.
        file_endings_avoid (str or tuple(str)): String or tuple of strings. Files with these endings
            will not be included.

    Returns:
        list(pathlib.Path): The files that are available in SVN.
    """
    excludes = [] if excludes is None else [exclude.resolve() for exclude in excludes]

    command = ["svn", "status", "-v"]
    output = subprocess.check_output(command, cwd=directory, universal_newlines=True)
    for line in output.split("\n"):
        match = RE_SVN_STATUS_LINE.match(line)
        if not match:
            continue

        svn_file = match.group(1)
        file_path = directory / svn_file

        # Make sure concatenation of relative paths worked
        assert file_path.exists(), file_path

        if file_path.is_dir():
            continue

        if file_endings_include is not None and not file_path.name.endswith(file_endings_include):
            continue

        if file_endings_avoid is not None and file_path.name.endswith(file_endings_avoid):
            continue

        if file_is_in_directory(file_path, excludes):
            continue

        yield file_path
