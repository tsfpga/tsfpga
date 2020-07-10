# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import subprocess
from os import makedirs
from os.path import exists

from tsfpga.sby_writer import SbyWriter


class YosysProject:
    """
    Used for handling a Yosys poject, synthesized with GHDL.
    Currently supports formal verification, but has no real build support.
    """

    def __init__(
            self,
            modules,
            top=None,
            generics=None,
            formal_settings=None,
    ):
        self.modules = modules
        self.top = top
        self.generics = generics
        self.formal_settings = formal_settings

    def run_formal(self, project_path, src_files, compilation_outputs):
        if not exists(project_path):
            makedirs(project_path)

        run_symbiyosys_sby = project_path / "run_symbiyosys.sby"
        SbyWriter.write_sby(
            run_symbiyosys_sby,
            self.top,
            self.generics,
            self.formal_settings,
            compilation_outputs,
            src_files)

        sby_cmd = ["sby", "--yosys", "yosys -m ghdl", "-f", str(run_symbiyosys_sby)]
        return subprocess.call(sby_cmd)
