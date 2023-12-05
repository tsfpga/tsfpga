# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# First party libraries
from tsfpga.module import BaseModule


class Module(BaseModule):
    version = 3

    def registers_hook(self):
        # Should have some registers already from the TOML file.
        register_list = self.registers
        assert register_list is not None

        register_list.add_constant(
            "version", self.version, f"Version number for the {self.name} module."
        )
        register_list.get_register("version").get_field("version").default_value = self.version
