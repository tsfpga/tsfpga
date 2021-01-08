# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


from .bit import Bit


class Mode:
    def __init__(self, mode_readable, description):
        self.mode_readable = mode_readable
        self.description = description


REGISTER_MODES = dict(
    r=Mode("Read", "Bus can read a value that fabric provides."),
    w=Mode("Write", "Bus can write a value that is available for fabric usage."),
    r_w=Mode(
        "Read, Write",
        "Bus can write a value and read it back. The written value is available for fabric usage.",
    ),
    wpulse=Mode(
        "Write-pulse", "Bus can write a value that is asserted for one clock cycle in fabric."
    ),
    r_wpulse=Mode(
        "Read, Write-pulse",
        "Bus can read a value that fabric provides. "
        "Bus can write a value that is asserted for one clock cycle in fabric.",
    ),
)


class Register:

    """
    Used to represent a register and its fields.
    """

    def __init__(self, name, index, mode, description=None, default_value=None):
        """
        Arguments:
            name (str): The name of the register.
            index (int): The zero-based index of this register in its register list.
            mode (str): A valid register mode.
            description (str): Textual register description.
            default_value (int): Default value for the register (signed).
        """
        if mode not in REGISTER_MODES:
            raise ValueError(f'Invalid mode "{mode}" for register "{name}"')

        self.name = name
        self.index = index
        self.mode = mode
        self.description = "" if description is None else description
        self.default_value = 0 if default_value is None else default_value
        self.bits = []

    def append_bit(self, name, description):
        """
        Append a bit to this register.

        Arguments:
            name (str): The name of the bit.
            description (str): Description of the bit.
        Return:
            :class:`.Bit`: The bit object that was created.
        """
        index = len(self.bits)
        bit = Bit(name, index, description)

        self.bits.append(bit)
        return bit

    @property
    def address(self):
        """
        int: Byte address, within the register list, of this register.
        """
        return 4 * self.index

    @property
    def is_bus_readable(self):
        """
        True if the register is readable by bus. Based on the register type.
        """
        return self.mode in ["r", "r_w", "r_wpulse"]

    @property
    def is_bus_writeable(self):
        """
        True if the register is writeable by bus. Based on the register type.
        """
        return self.mode in ["w", "r_w", "wpulse", "r_wpulse"]

    def __repr__(self):
        return f"""{self.__class__.__name__}(\
name={self.name},\
index={self.index},\
mode={self.mode},\
description={self.description},\
default_value={self.default_value},\
bits={','.join([repr(bit) for bit in self.bits])},\
)"""
