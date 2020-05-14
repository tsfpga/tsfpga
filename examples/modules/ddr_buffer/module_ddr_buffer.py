# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.module import BaseModule


class Module(BaseModule):

    version = "3"

    def registers_hook(self):
        self.registers.add_constant("version", self.version)
        self.registers.get_register("version").default_value = int(self.version)
