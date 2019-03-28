# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import dirname, abspath
import subprocess


def run_vivado_tcl(vivado_path, tcl_file, no_log_file=False):
    """
    Setting cwd ensures that any .log or .jou files produced are placed in
    the same directory as the TCL file that produced them.

    Subprocess has to be run with shell=True on Windows where vivado is a bat file.
    """
    cmd = "%s -mode batch -notrace -source %s" % (vivado_path, tcl_file)
    if no_log_file:
        cmd += " -nojournal -nolog"
    cwd = dirname(tcl_file)
    subprocess.check_call(cmd, cwd=cwd, shell=True)


def to_tcl_path(path):
    return abspath(path).replace("\\", "/")
