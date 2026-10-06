# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations


class StringGenericValue:
    """
    Use this type for generic values of type ``string``.
    """

    def __init__(self, value: str) -> None:
        """
        Arguments:
            value: A string of variable length with any content.
        """
        if not isinstance(value, str):
            raise TypeError(
                f"Expected {self.__class__.__name__} value to be of type str."
                f' Got type="{type(value)}", value="{value}".'
            )

        if " " in value:
            raise ValueError(
                f'Expected {self.__class__.__name__} value to not contain spaces. Got "{value}".'
            )

        self.value = value

    def __str__(self) -> str:
        return self.value


class BitVectorGenericValue:
    """
    Use this type for generic values of type ``std_logic_vector``.
    """

    def __init__(self, value: str) -> None:
        """
        Arguments:
            value: A string of variable length containing only "1" or "0".
        """
        if not isinstance(value, str):
            raise TypeError(
                f"Expected {self.__class__.__name__} value to be of type str."
                f' Got type="{type(value)}", value="{value}".'
            )

        for bit_value in value:
            if bit_value not in ["1", "0"]:
                raise ValueError(
                    f'Expected {self.__class__.__name__} value to contain only "1" or "0".'
                    f' Got "{value}".'
                )

        self.value = value

    @property
    def length(self) -> int:
        """
        The number of bits in the vector.
        """
        return len(self.value)

    def __str__(self) -> str:
        return self.value


#: A generic value of a native Python type, or one of the tsfpga wrapper classes above.
GenericValue = bool | int | float | StringGenericValue | BitVectorGenericValue

#: A mapping of generic name to :data:`.GenericValue`, as accepted by the build project classes.
GenericValues = dict[str, GenericValue]
