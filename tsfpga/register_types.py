# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


class Bit:

    """
    Used to represent a bit in a register.
    """

    def __init__(self, name, index, description):
        """
        Args:
            name (str): The name of the bit.
            index (int): The zero-based index of this bit within the register.
            description (str): Textual bit description.
        """
        self.name = name
        self.index = index
        self.description = description


class Register:

    """
    Used to represent a register and its fields.
    """

    def __init__(self, name, index, mode, description=""):
        """
        Args:
            name (str): The name of the register.
            index (int): The zero-based index of this register in its register list.
            mode (str): A valid register mode.
            description (str): Textual register description.
        """
        self.name = name
        self.index = index
        self.mode = mode
        self.description = description
        self.bits = []

    def append_bit(self, name, description):
        """
        Append a bit to this register.

        Args:
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


class RegisterArray:

    """
    Represent an array of registers. That is, a sequence of registers that shall be repeated a
    number of times in a register list.
    """

    def __init__(self, name, base_index, length):
        """
        Args:
            name (str): The name of this register array.
            base_index (int): The zero-based index of the first register of this array in
                the register list.
            length (int): The number of times the register sequence shall be repeated.
        """
        self.name = name
        self.base_index = base_index
        self.length = length
        self.registers = []

    def append_register(self, name, mode):
        """
        Append a register to this array.

        Args:
            name (str): The name of the register.
            mode (str): A valid register mode.
        Return:
            :class:`.Register`: The register object that was created.
        """
        index = len(self.registers)
        register = Register(name, index, mode)

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
