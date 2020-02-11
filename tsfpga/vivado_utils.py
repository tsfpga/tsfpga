# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import abspath, dirname, exists
import subprocess


def run_vivado_tcl(vivado_path, tcl_file, no_log_file=False):
    """
    Setting cwd ensures that any .log or .jou files produced are placed in
    the same directory as the TCL file that produced them.

    Subprocess has to be run with shell=True on Windows where vivado is a bat file.
    """
    cmd = f"{vivado_path} -mode batch -notrace -source {tcl_file}"
    if no_log_file:
        cmd += " -nojournal -nolog"
    subprocess.check_call(cmd, cwd=dirname(tcl_file), shell=True)


def run_vivado_gui(vivado_path, project_file):
    """
    Setting cwd ensures that any .log or .jou files produced are placed in
    the same directory as the project.

    Subprocess has to be run with shell=True on Windows where vivado is a bat file.
    """
    cmd = f"{vivado_path} -mode gui {project_file}"
    if not exists(project_file):
        raise FileNotFoundError(f"Project does not exist: {project_file}")
    subprocess.check_call(cmd, cwd=dirname(project_file), shell=True)


def to_tcl_path(path):
    return abspath(path).replace("\\", "/")
