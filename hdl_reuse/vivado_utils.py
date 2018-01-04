from hdl_reuse.system_utils import run_command


def run_vivado_tcl(vivado_path, tcl_file):
    cmd = [vivado_path, "-mode", "tcl", "-source", tcl_file, "-nojournal", "-nolog"]
    run_command(cmd)
