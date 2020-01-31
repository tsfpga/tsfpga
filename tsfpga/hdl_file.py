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

    def __init__(self, filename):
        """
        Args:
            filename: Path to a HDL source file.
        """
        self.filename = filename

    @property
    def is_vhdl(self):
        """
        Returns:
            True of the file is a VHDL file. Otherwise False.
        """
        return self.filename.endswith(self.vhdl_file_ending)

    @property
    def is_verilog_source(self):
        """
        Returns:
            True of the file is a Verilog source file. Otherwise False.
        """
        return self.filename.endswith(self.verilog_source_file_ending)

    @property
    def is_verilog_header(self):
        """
        Returns:
            True of the file is a Verilog header file. Otherwise False.
        """
        return self.filename.endswith(self.verilog_header_file_ending)
