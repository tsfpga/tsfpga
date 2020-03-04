# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


class HdlFile:

    """
    Class for representing a HDL source code file.
    """

    vhdl_file_ending = ".vhd"
    verilog_source_file_ending = ".v"
    verilog_header_file_ending = ".vh"
    file_endings = (vhdl_file_ending, verilog_source_file_ending, verilog_header_file_ending)

    def __init__(self, path):
        """
        Args:
            path (`pathlib.Path`): Path to a HDL source code  file.
        """
        self.path = path

    @property
    def is_vhdl(self):
        """
        True if the file is a VHDL file. Otherwise False.
        """
        return self.path.name.endswith(self.vhdl_file_ending)

    @property
    def is_verilog_source(self):
        """
        True if the file is a Verilog source file. Otherwise False.
        """
        return self.path.name.endswith(self.verilog_source_file_ending)

    @property
    def is_verilog_header(self):
        """
        True if the file is a Verilog header file. Otherwise False.
        """
        return self.path.name.endswith(self.verilog_header_file_ending)

    def __str__(self):
        return str(self.path)
