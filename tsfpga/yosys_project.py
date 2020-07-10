# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os import makedirs
from os.path import exists

from vunit.ostools import Process

from tsfpga.sby_writer import SbyWriter


class YosysProject:
    """
    Used for handling a Yosys poject, synthesized with GHDL.
    Currently supports formal verification, but has no real build support.
    """

    def __init__(
            self,
            top=None,
            generics=None,
            formal_settings=None,
    ):
        self.top = top
        self.generics = generics
        self.formal_settings = formal_settings

    def run_formal(self, project_path, src_files, compiled_libraries):
        if not exists(project_path):
            makedirs(project_path)

        run_symbiyosys_sby = project_path / "run_symbiyosys.sby"
        SbyWriter.write_sby(
            run_symbiyosys_sby,
            self.top,
            self.generics,
            self.formal_settings,
            compiled_libraries,
            src_files)

        sby_cmd = ["sby", "--yosys", "yosys -m ghdl", "-f", str(run_symbiyosys_sby)]

        try:
            proc = Process(sby_cmd)
            proc.consume_output()
            status = True
        except Process.NonZeroExitCode:
            status = False

        return status
