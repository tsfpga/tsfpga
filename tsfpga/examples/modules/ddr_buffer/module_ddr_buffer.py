# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# First party libraries
from tsfpga.module import BaseModule


class Module(BaseModule):
    # This will be much nicer when the register generator supports integer fields.
    # For now it is a bit vector field.
    version = "00000011"

    def registers_hook(self):
        self.registers.add_constant(
            "version", int(self.version, base=2), f"Version number for the {self.name} module."
        )
        self.registers.get_register("version").get_field("version").default_value = self.version
