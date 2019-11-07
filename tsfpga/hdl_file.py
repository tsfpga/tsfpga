# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


class HdlFile:

    vhdl_file_ending = ".vhd"
    verilog_source_file_ending = ".v"
    verilog_header_file_ending = ".vh"
    file_endings = (vhdl_file_ending, verilog_source_file_ending, verilog_header_file_ending)

    def __init__(self, filename):
        self.filename = filename

    @property
    def is_vhdl(self):
        return self.filename.endswith(self.vhdl_file_ending)

    @property
    def is_verilog_source(self):
        return self.filename.endswith(self.verilog_source_file_ending)

    @property
    def is_verilog_header(self):
        return self.filename.endswith(self.verilog_header_file_ending)
