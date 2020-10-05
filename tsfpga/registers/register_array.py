# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from .register import Register


class RegisterArray:

    """
    Represent an array of registers. That is, a sequence of registers that shall be repeated a
    number of times in a register list.
    """

    def __init__(self, name, base_index, length):
        """
        Arguments:
            name (str): The name of this register array.
            base_index (int): The zero-based index of the first register of this array in
                the register list.
            length (int): The number of times the register sequence shall be repeated.
        """
        self.name = name
        self.base_index = base_index
        self.length = length
        self.registers = []

    def append_register(self, name, mode, description=None, default_value=None):
        """
        Append a register to this array.

        Arguments:
            name (str): The name of the register.
            mode (str): A valid register mode.
            description (str): Textual register description.
            default_value (int): Default value for the register (signed).
        Return:
            :class:`.Register`: The register object that was created.
        """
        index = len(self.registers)
        register = Register(name, index, mode, description, default_value)

        self.registers.append(register)
        return register

    @property
    def index(self):
        """
        Property exists to be used analogously with ``Register.index``.

        Return:
            int: The highest index occupied by this array.
        """
        return self.base_index + self.length * len(self.registers) - 1

    def __repr__(self):
        return f"""{self.__class__.__name__}(\
name={self.name},\
base_index={self.base_index},\
length={self.length},\
registers={','.join([repr(register) for register in self.registers])},\
)"""
