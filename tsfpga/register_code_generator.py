# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.register_types import Register


class RegisterCodeGenerator:

    """
    Common functions for generating register code.
    """

    @staticmethod
    def _iterate_registers(register_objects):
        for register_object in register_objects:
            if isinstance(register_object, Register):
                yield (register_object, None)
            else:
                for register in register_object.registers:
                    yield (register, register_object)
