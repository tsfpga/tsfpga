# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


class StringGenericValue:
    """
    Use this type for generic values of type ``string``.
    """

    def __init__(self, value):
        """
        Arguments:
            value (str): A string of variable length with any content.
        """
        if not isinstance(value, str):
            raise ValueError(f"Expected {self.__class__.__name__} value to be of type str: {value}")

        if " " in value:
            raise ValueError(
                f"Expected {self.__class__.__name__} value to not contain spaces: {value}"
            )

        self.value = value

    def __str__(self):
        return self.value


class BitVectorGenericValue:
    """
    Use this type for generic values of type ``std_logic_vector``.
    """

    def __init__(self, value):
        """
        Arguments:
            value (str): A string of variable length containing only "1" or "0".
        """
        if not isinstance(value, str):
            raise ValueError(f"Expected {self.__class__.__name__} value to be of type str: {value}")

        for bit_value in value:
            if bit_value not in ["1", "0"]:
                raise ValueError(
                    f'Expected {self.__class__.__name__} value to contain only "1" or "0": {value}'
                )

        self.value = value

    @property
    def length(self):
        """
        int: The number of bits in the vector.
        """
        return len(self.value)

    def __str__(self):
        return self.value


def get_vivado_tcl_generic_value(value):
    """
    Convert generic values of different types to the format recognized by Vivado TCL:
    https://www.xilinx.com/support/answers/52217.html

    Arguments:
        value (bool, int, float, StringGenericValue, BitVectorGenericValue): A generic value.
    """
    # Note that bool is a sub-class of int in Python, so check for bool must be first
    if isinstance(value, bool):
        return f"1'b{int(value)}"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        return str(value)

    if isinstance(value, BitVectorGenericValue):
        return f"{value.length}'b{value.value}"

    if isinstance(value, StringGenericValue):
        return value.value

    raise ValueError(f"Got unsupported type for generic. Type={type(value)}, value={value}.")
