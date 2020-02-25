# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from pathlib import Path
from shutil import which
import subprocess


def run_vivado_tcl(vivado_path, tcl_file, no_log_file=False):
    """
    Setting cwd ensures that any .log or .jou files produced are placed in
    the same directory as the TCL file that produced them.

    Subprocess has to be run with shell=True on Windows where vivado is a bat file.

    Args:
        vivado_path (`pathlib.Path`): Path to Vivado executable. Can set to None
            to use whatever version is in PATH.
        tcl_file (`pathlib.Path`): Path to TCL file.
    """
    tcl_file = tcl_file.resolve()
    cmd = f"{get_vivado_path(vivado_path)} -mode batch -notrace -source {tcl_file}"
    if no_log_file:
        cmd += " -nojournal -nolog"
    subprocess.check_call(cmd, cwd=tcl_file.parent, shell=True)


def run_vivado_gui(vivado_path, project_file):
    """
    Setting cwd ensures that any .log or .jou files produced are placed in
    the same directory as the project.

    Subprocess has to be run with shell=True on Windows where vivado is a bat file.

    Args:
        vivado_path (`pathlib.Path`): Path to Vivado executable. Can set to None
            to use whatever version is in PATH.
        project_file (`pathlib.Path`): Path to a project .xpr file.
    """
    project_file = project_file.resolve()
    cmd = f"{get_vivado_path(vivado_path)} -mode gui {project_file}"
    if not project_file.exists():
        raise FileNotFoundError(f"Project does not exist: {project_file}")
    subprocess.check_call(cmd, cwd=project_file.parent, shell=True)


def get_vivado_path(vivado_path=None):
    """
    Wrapper to get a ``pathlib.Path`` to vivado executable.

    Args:
        vivado_path (`pathlib.Path`): Path to vivado executable. Set to None to use whatever
            is available in PATH.
    """
    if vivado_path is not None:
        return vivado_path.resolve()

    which_vivado = which("vivado")
    if which_vivado is None:
        raise FileNotFoundError("Could not find vivado on PATH")

    return Path(which_vivado).resolve()


def to_tcl_path(path):
    """
    Return a path string in a format suitable for TCL.
    """
    return str(path.resolve()).replace("\\", "/")
