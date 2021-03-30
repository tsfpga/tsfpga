# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


from .bit import Bit


class RegisterMode:
    def __init__(self, mode_readable, description):
        self.mode_readable = mode_readable
        self.description = description


REGISTER_MODES = dict(
    r=RegisterMode("Read", "Bus can read a value that fabric provides."),
    w=RegisterMode("Write", "Bus can write a value that is available for fabric usage."),
    r_w=RegisterMode(
        "Read, Write",
        "Bus can write a value and read it back. The written value is available for fabric usage.",
    ),
    wpulse=RegisterMode(
        "Write-pulse", "Bus can write a value that is asserted for one clock cycle in fabric."
    ),
    r_wpulse=RegisterMode(
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
        self.bit_index = 0

    @staticmethod
    def signed2unsigned(num, width):
        """
        Calculates two's complement of integer when needed.

        Arguments:
            num (int) : Number to be converted.
            width (int) : Required number of output bits
        """
        result = 0
        if num:
            result = (-num ^ (2 ** width - 1)) + 1 if num < 0 else num
        return result

    def append_bit(self, name, description, width=1, default_value=None):
        """
        Append a bit field to this register.

        Arguments:
            name (str): The name of the bit field.
            width (int) : The width of the bit field.
            description (str): Description of the bit.
        Return:
            :class:`.Bit`: The bit array object that was created.
        """

        if width < 1 or width > 32:
            raise ValueError(f'Invalid bit array width for register "{self.name}"')

        value = self.signed2unsigned(default_value, width)
        self.default_value += value * 2 ** self.bit_index

        bits = Bit(name, self.bit_index, description, width, value)
        self.bits.append(bits)

        self.bit_index += width
        if self.bit_index > 32:
            raise ValueError(f'Maximum width exceeded for register "{self.name}"')

        return bits

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
