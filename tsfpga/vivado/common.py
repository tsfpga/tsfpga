# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path
from shutil import which
from typing import Optional

# Third party libraries
from vunit.ostools import Process

# First party libraries
from tsfpga.git_utils import get_git_sha
from tsfpga.math_utils import to_binary_string


def run_vivado_tcl(vivado_path: Optional[Path], tcl_file: Path, no_log_file: bool = False) -> bool:
    """
    Setting cwd ensures that any .log or .jou files produced are placed in
    the same directory as the TCL file that produced them.

    Arguments:
        vivado_path: Path to Vivado executable. Can set to ``None``
            to use whatever version is in ``PATH``.
        tcl_file: Path to TCL file.
        no_log_file: Optionally set Vivado flags to not create log and journal files.

    Return:
        True if everything went well.
    """
    tcl_file = tcl_file.resolve()

    cmd = [
        str(get_vivado_path(vivado_path)),
        "-mode",
        "batch",
        "-notrace",
        "-source",
        str(tcl_file),
    ]
    if no_log_file:
        cmd += ["-nojournal", "-nolog"]

    try:
        Process(args=cmd, cwd=tcl_file.parent).consume_output()
    except Process.NonZeroExitCode:
        return False
    return True


def run_vivado_gui(vivado_path: Optional[Path], project_file: Path) -> bool:
    """
    Setting cwd ensures that any .log or .jou files produced are placed in
    the same directory as the project.

    Arguments:
        vivado_path: Path to Vivado executable.
            Leave as ``None`` to use whatever is available in the system ``PATH``.
        project_file: Path to a project .xpr file.

    Return:
        True if everything went well.
    """
    project_file = project_file.resolve()
    if not project_file.exists():
        raise FileNotFoundError(f"Project does not exist: {project_file}")

    cmd = [str(get_vivado_path(vivado_path)), "-mode", "gui", str(project_file)]

    try:
        Process(args=cmd, cwd=project_file.parent).consume_output()
    except Process.NonZeroExitCode:
        return False
    return True


def get_vivado_path(vivado_path: Optional[Path] = None) -> Path:
    """
    Wrapper to get a path to Vivado executable.

    Arguments:
        vivado_path: Path to vivado executable.
            Leave as ``None`` to use whatever is available in the system ``PATH``.
    """
    if vivado_path is not None:
        return vivado_path.resolve()

    which_vivado = which("vivado")
    if which_vivado is None:
        raise FileNotFoundError("Could not find vivado on PATH")

    return Path(which_vivado).resolve()


def get_vivado_version(vivado_path: Optional[Path] = None) -> str:
    """
    Get the version number of the Vivado installation.

    Arguments:
        vivado_path: Path to vivado executable.
            Leave as ``None`` to use whatever is available in the system ``PATH``.

    Return:
        The version, e.g. ``"2021.2"``.
    """
    vivado_path = get_vivado_path(vivado_path=vivado_path)

    # E.g. "/home/lukas/work/Xilinx/Vivado/2021.2/bin/vivado" -> "2021.2"
    vivado_version = vivado_path.parent.parent.name

    return vivado_version


def get_git_sha_slv(git_directory: Path) -> tuple[str, str]:
    """
    Get the current git SHA encoded as 32-character binary strings. Suitable for setting
    as ``std_logic_vector`` generics to a Vivado build, where they can be assigned to
    software-accessible registers to keep track of what revision an FPGA was built from.

    Will return the left-most 16 characters of the git SHA, encoded into two 32-character
    binary strings.

    Arguments:
        directory: The directory where git commands will be run.

    Return:
        First object in tuple is the left-most eight characters of the git SHA
        encoded as a 32-character binary string.
        Second object is the next eight characters from the git SHA.
    """
    git_sha = get_git_sha(directory=git_directory)
    assert len(git_sha) == 16

    def hex_to_binary_string(hex_string: str) -> str:
        assert len(hex_string) == 8
        int_value = int(hex_string, base=16)

        return to_binary_string(value=int_value, result_width=32)

    left_binary_string = hex_to_binary_string(hex_string=git_sha[0:8])
    right_binary_string = hex_to_binary_string(hex_string=git_sha[8:16])

    return (left_binary_string, right_binary_string)


def to_tcl_path(path: Path) -> str:
    """
    Return a path string in a format suitable for TCL.
    """
    return str(path.resolve()).replace("\\", "/")
