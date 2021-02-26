# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from tsfpga.module import BaseModule


class Module(BaseModule):

    version = 3

    def registers_hook(self):
        self.registers.add_constant(
            "version", self.version, f"Version number for the {self.name} module."
        )
        self.registers.get_register("version").default_value = int(self.version)
