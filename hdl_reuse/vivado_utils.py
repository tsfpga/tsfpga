from os.path import dirname

from hdl_reuse.system_utils import run_command


def run_vivado_tcl(vivado_path, tcl_file, no_log_file=False):
    """
    Setting cwd ensures that any .log or .jou files produced are placed in
    the same directory as the TCL file that produced them.
    """
    cmd = [vivado_path, "-mode", "tcl", "-source", tcl_file]
    if no_log_file:
        cmd += ["-nojournal", "-nolog"]
    cwd = dirname(tcl_file)
    run_command(cmd, cwd=cwd)
